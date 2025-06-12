#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time 
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import faiss
from collections import defaultdict 
import logging
from memory.document_processor import DocumentProcessor
from utils import get_keys
# --- Setup Logging ---
logger = logging.getLogger(__name__)
# Optional: Set a handler if not configured elsewhere (e.g., for standalone testing)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- Global Weights and Definitions ---
LAYER_WEIGHTS = {
    "global": 1.0,
    "event": 1.0,
    "summary": 1.0,
}
TAG_WEIGHTS = {
    # setting layer
    "profile": 1.5,
    "scene_init": 1.3,
    "scene_objective": 1.4,

    # event_raw layer
    "conversation": 1.0,

    # event_summary layer
    "summary_conversation": 1.2, # Summaries might be slightly more important than raw convo
    "summary_scene_init": 1.1,
    "summary_scene_objective": 1.3,

    # archived layer
    "archived_conversation": 0.2, # Low weight for archived items
    "archived_scene_init": 0.1,
    "archived_scene_objective": 0.1,
}
TEXT_WEIGHT = 0.5
TAG_EMBEDDING_WEIGHT = 0.5 

class MemoryPiece:
    def __init__(self, piece_id, text="", layer="global", tag="conversation", metadata=None, layer_id=None, scene_id=None):
        self.id = piece_id
        self.text = text
        self.layer = layer
        self.tag = tag if tag else layer 
        self.metadata = metadata or {}
        self.layer_id = layer_id
        self.scene_id = scene_id

    def __repr__(self):
        return f"MemoryPiece(id={self.id}, layer='{self.layer}', tag='{self.tag}', layer_id={self.layer_id}, scene_id={self.scene_id}, text='{self.text[:30]}...')"

class MemoryChunk:
    def __init__(self, chunk_id, pieces_list, layer="global", tag=None, metadata=None, layer_id=None, scene_id=None):
        self.id = chunk_id
        self.pieces = pieces_list 
        self.text = " ".join([p.text.strip() for p in pieces_list]) 
        self.layer = layer
        self.metadata = metadata or {}
        self.layer_id = layer_id
        self.embedding = None
        self.scene_id = scene_id
        self.tag = tag if tag else layer 
        self.tag_embedding = None
        
        self.max_pieces = 5 
        self.max_text_length = 500 

    def __repr__(self):
        return f"MemoryChunk(id={self.id}, layer='{self.layer}', tag='{self.tag}', layer_id={self.layer_id}, scene_id={self.scene_id}, #pieces={len(self.pieces)}, text='{self.text[:50]}...')"

    def add_piece(self, piece, embed_model, tag_embeddings):
        if len(self.pieces) >= self.max_pieces or \
           len(self.text) + len(piece.text) + 1 > self.max_text_length: 
            logger.info(f"Chunk {self.id} is full (pieces:{len(self.pieces)}/{self.max_pieces}, len:{len(self.text)}/{self.max_text_length}). Cannot add piece {piece.id}.")
            return False
        
        self.pieces.append(piece)
        self.text += " " + piece.text.strip() 
        self.set_embedding(embed_model, tag_embeddings) 
        logger.info(f"Added piece {piece.id} to chunk {self.id}. New text length: {len(self.text)}")
        return True

    def set_embedding(self, embed_model, tag_embeddings):
        text_embedding = embed_model.encode(self.text).astype('float32')
        
        if self.tag not in tag_embeddings:
            logger.warning(f"Tag '{self.tag}' not preloaded. Encoding on the fly.")
            tag_embeddings[self.tag] = embed_model.encode(self.tag).astype('float32')
        
        self.tag_embedding = tag_embeddings[self.tag]
        
        self.embedding = (TEXT_WEIGHT * text_embedding + TAG_EMBEDDING_WEIGHT * self.tag_embedding).astype('float32')

# --- New: Base Memory Sub-Storage Class ---
class BaseMemorySubStorage:
    def __init__(self, parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces):
        self.parent_storage = parent_storage
        self.chunks = {}  # {chunk_id: MemoryChunk object}
        self.next_chunk_id = 0 
        self.all_pieces_ordered = [] # Only for overlap logic within this sub-storage
        
        self.documents_for_bm25 = []  
        self.chunk_id_to_bm25_internal_idx = {}

        self.embed_model = embed_model
        self.dimension = dimension
        self.faiss_index = faiss.IndexIDMap(faiss.IndexFlatL2(self.dimension)) 
        self.bm25 = None
        self.tag_embeddings = tag_embeddings

        self.chunk_max_pieces = chunk_max_pieces 
        self.chunk_overlap_pieces = min(chunk_overlap_pieces, chunk_max_pieces - 1) 
        if self.chunk_overlap_pieces < 0: self.chunk_overlap_pieces = 0

    def _create_and_add_new_chunk(self, pieces_list, layer, tag, metadata, scene_id, piece_id_for_logging):
        chunk_id = self.parent_storage._get_next_global_chunk_id()

        chunk = MemoryChunk(chunk_id, pieces_list=pieces_list, layer=layer, tag=tag, 
                            metadata=metadata, layer_id=None, scene_id=scene_id) # layer_id handled by main storage
        
        chunk.max_pieces = self.chunk_max_pieces 
        chunk.set_embedding(self.embed_model, self.tag_embeddings)
        
        self.chunks[chunk_id] = chunk
        
        bm25_doc_text = f"{layer}:{chunk.text}" 
        self.documents_for_bm25.append(DocumentProcessor().tokenize_text(bm25_doc_text))
        self.chunk_id_to_bm25_internal_idx[chunk_id] = len(self.documents_for_bm25) - 1 

        vec = np.array([chunk.embedding]).astype('float32')
        self.faiss_index.add_with_ids(vec, np.array([chunk_id]))

        self.build_bm25() 
        logger.info(f"[{type(self).__name__}] Created new chunk {chunk.id} (L:{layer}, T:{tag}, S:{scene_id}) with {len(pieces_list)} pieces for piece {piece_id_for_logging}.")
        return chunk

    def add_piece_to_sub_storage(self, piece, next_layer_id_for_piece):
        """Adds a piece to this sub-storage, handling chunking and overlap."""
        # Update piece's layer_id before storing globally
        piece.layer_id = next_layer_id_for_piece # layer_id represents the order of the piece in the sub-storage
        self.all_pieces_ordered.append(piece) 

        found_suitable_chunk = False
        most_recent_suitable_chunk = None

        for chunk_id_candidate in reversed(sorted(self.chunks.keys())): 
            chunk = self.chunks[chunk_id_candidate]
            # Criteria for suitability: same layer, same scene_id (if applicable), same tag
            # Note: For Global memories (profile, global), scene_id might be None, so check accordingly
            is_suitable = chunk.layer == piece.layer and chunk.tag == piece.tag
            if piece.scene_id is not None:
                is_suitable = is_suitable and (chunk.scene_id == piece.scene_id)
            elif chunk.scene_id is not None: # piece.scene_id is None, but chunk.scene_id is not
                is_suitable = False # Cannot merge scene-less with scene-specific chunks

            if is_suitable:
                most_recent_suitable_chunk = chunk
                break 

        if most_recent_suitable_chunk:
            if most_recent_suitable_chunk.add_piece(piece, self.embed_model, self.tag_embeddings):
                chunk_id = most_recent_suitable_chunk.id
                vec = np.array([most_recent_suitable_chunk.embedding]).astype('float32')
                
                self.faiss_index.remove_ids(np.array([chunk_id])) 
                self.faiss_index.add_with_ids(vec, np.array([chunk_id])) 
                
                bm25_internal_idx = self.chunk_id_to_bm25_internal_idx[chunk_id]
                self.documents_for_bm25[bm25_internal_idx] = \
                    DocumentProcessor().tokenize_text(f"{most_recent_suitable_chunk.layer}:{most_recent_suitable_chunk.text}")
                self.build_bm25() 
                
                found_suitable_chunk = True
        
        if not found_suitable_chunk:
            pieces_for_new_chunk = []
            
            overlap_count = 0
            for p_idx in range(len(self.all_pieces_ordered) - 2, -1, -1): 
                if overlap_count >= self.chunk_overlap_pieces:
                    break
                prev_piece = self.all_pieces_ordered[p_idx]
                # Only include pieces in overlap that match the new chunk's characteristics
                is_overlap_suitable = prev_piece.layer == piece.layer and prev_piece.tag == piece.tag
                if piece.scene_id is not None:
                    is_overlap_suitable = is_overlap_suitable and (prev_piece.scene_id == piece.scene_id)
                elif prev_piece.scene_id is not None:
                    is_overlap_suitable = False # Cannot merge scene-less with scene-specific chunks
                
                if is_overlap_suitable:
                    pieces_for_new_chunk.insert(0, prev_piece) 
                    overlap_count += 1
            
            pieces_for_new_chunk.append(piece) 

            new_chunk = self._create_and_add_new_chunk(
                pieces_list=pieces_for_new_chunk, 
                layer=piece.layer, tag=piece.tag, metadata=piece.metadata, scene_id=piece.scene_id,
                piece_id_for_logging=piece.id
            )
            return new_chunk.id # Return the ID of the newly created chunk
        return None # Indicate no new chunk was created

    def add_chunk_to_sub_storage(self, piece, next_layer_id_for_piece):
        """Directly adds a new chunk with no overlap from previous chunks."""
        piece.layer_id = next_layer_id_for_piece # Update piece's layer_id
        self.all_pieces_ordered.append(piece) # Still add to global list for consistency
        
        chunk = self._create_and_add_new_chunk(
            pieces_list=[piece], 
            layer=piece.layer, tag=piece.tag, metadata=piece.metadata, scene_id=piece.scene_id,
            piece_id_for_logging=piece.id
        )
        logger.info(f"[{type(self).__name__}] Directly added new chunk {chunk.id} with text '{piece.text[:30]}...'")
        return chunk.id

    def build_bm25(self):
        if self.documents_for_bm25:
            self.bm25 = BM25Okapi(self.documents_for_bm25)
            logger.info(f"[{type(self).__name__}] BM25 index rebuilt.")
        else:
            self.bm25 = None
            logger.warning(f"[{type(self).__name__}] No documents for BM25. BM25 index is None.")
            
    def get_chunk(self, chunk_id):
        return self.chunks.get(chunk_id)

    def retrieve(self, query_text, current_scene_id, top_k, bm25_weight, vector_weight):
        """
        Retrieves relevant chunks from this sub-storage.
        This is a base retrieval, specific sub-classes might override or extend this.
        Returns a list of {'score': score, 'chunk': chunk} dicts.
        """
        tokenized_query = DocumentProcessor().tokenize_text(query_text)
        
        bm25_scores_by_chunk_id = {}
        if self.bm25 and self.documents_for_bm25:
            bm25_scores_raw = self.bm25.get_scores(tokenized_query)
            for chunk_id, internal_idx in self.chunk_id_to_bm25_internal_idx.items():
                if internal_idx < len(bm25_scores_raw):
                    bm25_scores_by_chunk_id[chunk_id] = bm25_scores_raw[internal_idx]
        else:
            logger.warning(f"[{type(self).__name__}] BM25 index not built or no documents.")

        query_embedding = self.embed_model.encode(query_text)
        vec = np.array([query_embedding]).astype('float32')
        
        vector_scores_by_chunk_id = defaultdict(float)
        num_docs_in_faiss = self.faiss_index.ntotal

        if num_docs_in_faiss > 0:
            actual_faiss_k = min(top_k * 5, num_docs_in_faiss) # Search a larger k to get enough candidates
            faiss_distances, faiss_chunk_ids = self.faiss_index.search(vec, actual_faiss_k)
            
            if faiss_chunk_ids.size > 0:
                for dist, chunk_id in zip(faiss_distances[0], faiss_chunk_ids[0]):
                    vector_scores_by_chunk_id[chunk_id] = 1.0 / (dist + 1e-9)
        else:
            logger.warning(f"[{type(self).__name__}] FAISS index is empty.")

        scored_chunks_info = []
        for chunk_id, chunk in self.chunks.items():
            bm25_s = bm25_scores_by_chunk_id.get(chunk_id, 0.0)
            vector_s = vector_scores_by_chunk_id.get(chunk_id, 0.0)

            base_score = (bm25_weight * bm25_s) + (vector_weight * vector_s)
            
            if base_score <= 1e-6: 
                continue

            # Apply layer/tag specific weights
            layer_weight = LAYER_WEIGHTS.get(chunk.layer, 1.0) * TAG_WEIGHTS.get(chunk.tag, 1.0)
            final_score = base_score * layer_weight

            if current_scene_id is not None and chunk.scene_id is not None and chunk.scene_id != current_scene_id:
                scene_diff = abs(current_scene_id - chunk.scene_id)
                inter_scene_recency_weight = 1.0 / (1 + 0.25 * scene_diff)
                final_score *= inter_scene_recency_weight
                logger.info(f"  [{type(self).__name__}] Inter-scene Recency (diff {scene_diff}): {inter_scene_recency_weight:.2f} -> Score: {final_score:.4f}")

            scored_chunks_info.append({'score': final_score, 'chunk': chunk})
        
        # Sort and return top_k
        sorted_by_score = sorted(scored_chunks_info, key=lambda x: x['score'], reverse=True)
        return sorted_by_score[:top_k]

# --- Specific Sub-Storage Implementations ---
class GlobalMemorySubStorage(BaseMemorySubStorage):
    def __init__(self, parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces):
        super().__init__(parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces)
        self.supported_tags = ["profile", "scene_init", "scene_objective"]

    def retrieve(self, query_text, current_scene_id, top_k, bm25_weight, vector_weight):
        # Global memories don't have scene-specific recency, so pass None for current_scene_id to super
        return super().retrieve(query_text, None, top_k, bm25_weight, vector_weight)


class EventMemorySubStorage(BaseMemorySubStorage):
    def __init__(self, parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces):
        super().__init__(parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces)
        self.supported_tags = ["conversation", "action", "thought", "archived_conversation", "archived_scene_init", "archived_scene_objective"]
        self.scene_conversation_chunks = defaultdict(list) # Ordered list of conversation chunk IDs per scene

    def add_piece_to_sub_storage(self, piece, next_layer_id_for_piece):
        new_chunk_id = super().add_piece_to_sub_storage(piece, next_layer_id_for_piece)
        if new_chunk_id is not None and piece.layer == "conversation":
            self.scene_conversation_chunks[piece.scene_id].append(new_chunk_id)
        return new_chunk_id

    def add_chunk_to_sub_storage(self, piece, next_layer_id_for_piece):
        new_chunk_id = super().add_chunk_to_sub_storage(piece, next_layer_id_for_piece)
        if new_chunk_id is not None and piece.layer == "conversation":
            self.scene_conversation_chunks[piece.scene_id].append(new_chunk_id)
        return new_chunk_id

    def get_dialogue_turns_ago(self, current_scene_id, chunk_id):
        if current_scene_id not in self.scene_conversation_chunks:
            return 0
        
        scene_dialogue_chunk_ids = self.scene_conversation_chunks[current_scene_id]
        try:
            idx = scene_dialogue_chunk_ids.index(chunk_id)
            turns_ago = len(scene_dialogue_chunk_ids) - 1 - idx
            return turns_ago
        except ValueError:
            return 0

    def retrieve(self, query_text, current_scene_id, top_k, bm25_weight, vector_weight):
        raw_results = super().retrieve(query_text, current_scene_id, top_k * 2, bm25_weight, vector_weight) # Get more candidates
        
        final_results = []
        for item in raw_results:
            chunk = item['chunk']
            final_score = item['score']

            # Apply inter-scene recency (if applicable for events)
            if current_scene_id is not None and chunk.scene_id is not None and chunk.scene_id != current_scene_id:
                scene_diff = abs(current_scene_id - chunk.scene_id)
                inter_scene_recency_weight = 1.0 / (1 + 0.25 * scene_diff)
                final_score *= inter_scene_recency_weight
                logger.info(f"  [EventMemorySubStorage] Inter-scene Recency (diff {scene_diff}): {inter_scene_recency_weight:.2f} -> Score: {final_score:.4f}")
            
            # Apply intra-scene dialogue recency specifically for conversation chunks within the current scene
            if current_scene_id is not None and chunk.scene_id == current_scene_id and \
               (chunk.layer == "conversation" or chunk.layer.startswith("summary_conversation")): # Also consider summary conversation as related to recency
                dialogue_turns_ago = self.get_dialogue_turns_ago(current_scene_id, chunk.id)
                if dialogue_turns_ago > 0: 
                    K_dialogue_turn_recency = 0.005 
                    intra_scene_dialogue_weight = 1.0 / (1 + K_dialogue_turn_recency * dialogue_turns_ago)
                    final_score *= max(0.2, intra_scene_dialogue_weight) 
                    logger.info(f"  [EventMemorySubStorage] Intra-Scene Recency (Turns ago: {dialogue_turns_ago}): {intra_scene_dialogue_weight:.4f} -> Score: {final_score:.4f}")
            
            final_results.append({'score': final_score, 'chunk': chunk})
        
        # Re-sort after applying specific weights
        final_results_sorted = sorted(final_results, key=lambda x: x['score'], reverse=True)
        return final_results_sorted[:top_k]

class SummaryMemorySubStorage(BaseMemorySubStorage):
    def __init__(self, parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces):
        super().__init__(parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces)
        self.supported_tags = ["summary_conversation", "summary_scene_init", "summary_scene_objective"]

    def retrieve(self, query_text, current_scene_id, top_k, bm25_weight, vector_weight):
        # Summary memories might also benefit from inter-scene recency if they are scene-specific
        raw_results = super().retrieve(query_text, current_scene_id, top_k * 2, bm25_weight, vector_weight)
        
        final_results = []
        for item in raw_results:
            chunk = item['chunk']
            final_score = item['score']

            if current_scene_id is not None and chunk.scene_id is not None and chunk.scene_id != current_scene_id:
                scene_diff = abs(current_scene_id - chunk.scene_id)
                inter_scene_recency_weight = 1.0 / (1 + 0.25 * scene_diff)
                final_score *= inter_scene_recency_weight
                logger.info(f"  [SummaryMemorySubStorage] Inter-scene Recency (diff {scene_diff}): {inter_scene_recency_weight:.2f} -> Score: {final_score:.4f}")
            
            final_results.append({'score': final_score, 'chunk': chunk})
        
        final_results_sorted = sorted(final_results, key=lambda x: x['score'], reverse=True)
        return final_results_sorted[:top_k]


# --- Main Memory Storage (Aggregator) ---
class MemoryStorage:
    def __init__(self, embed_model_name="all-MiniLM-L6-v2", chunk_max_pieces=5, chunk_overlap_pieces=1):
        self.embed_model = SentenceTransformer(embed_model_name)
        self.dimension = self.embed_model.get_sentence_embedding_dimension()
        self.tag_embeddings = {}
        self._preload_tag_embeddings()

        self.next_piece_id = 0
        self.next_layer_id = defaultdict(int) 
        self.next_global_chunk_id = 0 # <--- NEW: Global chunk ID counter


        self.global_storage = GlobalMemorySubStorage(self, self.embed_model, self.dimension, self.tag_embeddings, chunk_max_pieces, chunk_overlap_pieces)
        self.event_storage = EventMemorySubStorage(self, self.embed_model, self.dimension, self.tag_embeddings, chunk_max_pieces, chunk_overlap_pieces)
        self.summary_storage = SummaryMemorySubStorage(self, self.embed_model, self.dimension, self.tag_embeddings, chunk_max_pieces, chunk_overlap_pieces)

        self.all_sub_storages = {
            "global": self.global_storage,
            "event": self.event_storage,
            "summary": self.summary_storage
        }

        # self.tag_to_storage_map = {}
        # for storage_type, sub_storage in self.all_sub_storages.items():
        #     for tag in sub_storage.supported_tags:
        #         self.tag_to_storage_map[tag] = sub_storage

    def _get_next_global_chunk_id(self): # <--- NEW method
        new_id = self.next_global_chunk_id
        self.next_global_chunk_id += 1
        return new_id

    def _preload_tag_embeddings(self):
        logger.info("Preloading tag embeddings...")
        for tag in get_keys(TAG_WEIGHTS):
            self.tag_embeddings[tag] = self.embed_model.encode(tag).astype('float32')
        logger.info("TAG embeddings preloaded.")

    # def _get_sub_storage_for_tag(self, tag):
    #     print(self.tag_to_storage_map)
    #     sub_storage = self.tag_to_storage_map.get(tag)
    #     if not sub_storage:
    #         raise ValueError(f"No sub-storage defined for tag: {tag}")
    #     return sub_storage
    def _get_sub_storage_for_layer(self, layer):
        return self.all_sub_storages[layer]

    def add_piece(self, text, layer, tag=None, metadata=None, scene_id=None):
        piece_id = self.next_piece_id
        self.next_piece_id += 1
        
        piece = MemoryPiece(piece_id, text, layer, tag, metadata, layer_id=None, scene_id=scene_id)
        
        sub_storage = self._get_sub_storage_for_layer(layer)
        return sub_storage.add_piece_to_sub_storage(piece, self.next_layer_id[layer])

    def add_chunk(self, text, layer, tag=None, metadata=None, scene_id=None):
        piece_id = self.next_piece_id
        self.next_piece_id += 1
        
        single_piece = MemoryPiece(piece_id, text, layer, tag, metadata, layer_id=None, scene_id=scene_id)
        
        sub_storage = self._get_sub_storage_for_layer(layer)
        return sub_storage.add_chunk_to_sub_storage(single_piece, self.next_layer_id[layer])

    def all_chunks(self):
        """Returns all chunks from all sub-storages for inspection."""
        all_chunks = {}
        for sub_storage in self.all_sub_storages.values():
            all_chunks.update(sub_storage.chunks)
        return list(all_chunks.values())
    
    def get_chunk(self, chunk_id):
        """Attempts to get a chunk by ID from any sub-storage."""
        for sub_storage in self.all_sub_storages.values():
            chunk = sub_storage.get_chunk(chunk_id)
            if chunk:
                return chunk
        return None


# --- Retriever Class (modified to use sub-storages) ---
class Retriever:
    def __init__(self, storage, top_k=5, bm25_weight=0.5, vector_weight=0.5):
        self.storage = storage # This is now the main MemoryStorage aggregating sub-storages
        self.top_k = top_k
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight

    # def retrieve_layered_draft(self, input_text, current_scene_id=None, desired_layers=None):
    #     if desired_layers is None:
    #         desired_layers = list(LAYER_WEIGHTS.keys())

    #     retrieved_chunks_by_layer = defaultdict(list)
        
    #     # Map desired layers to their respective sub-storages
    #     sub_storages_to_query = defaultdict(list)
    #     for layer in desired_layers:
    #         sub_storage = self.storage.tag_to_storage_map.get(layer)
    #         if sub_storage:
    #             sub_storages_to_query[sub_storage].append(layer)
    #         else:
    #             logger.warning(f"No sub-storage found for desired layer: {layer}. Skipping.")

    #     # Perform independent retrieval for each relevant sub-storage
    #     all_results_combined = []
    #     for sub_storage, layers_in_sub_storage in sub_storages_to_query.items():
    #         logger.info(f"\n--- Retrieving from {type(sub_storage).__name__} for layers: {layers_in_sub_storage} ---")
    #         # Retrieve from sub-storage. It will apply its internal weights and return top_k
    #         # We ask for top_k * 2 to give some room for filtering/re-ranking later if needed
    #         sub_storage_results = sub_storage.retrieve(
    #             query_text=input_text, 
    #             current_scene_id=current_scene_id, 
    #             top_k=self.top_k * 2, # Fetch more to allow for final filtering/re-ranking
    #             bm25_weight=self.bm25_weight, 
    #             vector_weight=self.vector_weight
    #         )
            
    #         # Since sub_storage.retrieve already returns a sorted list of {'score': score, 'chunk': chunk}
    #         # we just need to add them to a combined list
    #         all_results_combined.extend(sub_storage_results)

    #     # Final filtering and grouping by desired_layers (within the originally requested layers)
    #     final_layered_results = defaultdict(list)
        
    #     # Sort all combined results by score one last time
    #     sorted_all_results = sorted(all_results_combined, key=lambda x: x['score'], reverse=True)

    #     # Distribute into desired_layers, taking top_k for each.
    #     # This approach ensures each layer gets its own top_k
    #     # If you want a global top_k across ALL layers, this part would change.
    #     # Given your request for "每一部分可以内部使用tag权重加和检索...但是都是独立检索",
    #     # the current logic of filling `final_layered_results` per layer seems appropriate.
        
    #     # To ensure each layer gets its top_k from the combined pool of relevant results,
    #     # we iterate through the globally sorted list and add to the specific layer's list
    #     # until its top_k is reached. This is a common way to do it.
    #     # Alternatively, you could just return `sorted_all_results[:self.top_k]`
    #     # if you want a single global top_k regardless of layer.
        
    #     # For now, let's stick to returning top_k for each desired layer,
    #     # ensuring the items from each layer are highly relevant within that layer's context.
        
    #     temp_layered_results = defaultdict(list) # To store all relevant chunks before final top_k per layer
    #     for item in sorted_all_results:
    #         chunk = item['chunk']
    #         if chunk.layer in desired_layers:
    #             temp_layered_results[chunk.layer].append(item)
        
    #     for layer in desired_layers:
    #         # Sort within each layer (already sorted by overall score, but good for clarity)
    #         layer_chunks_sorted = sorted(temp_layered_results[layer], key=lambda x: x['score'], reverse=True)
    #         final_layered_results[layer] = [info['chunk'] for info in layer_chunks_sorted[:self.top_k]]
            
    #         logger.info(f"\n--- Top {self.top_k} Retrieved Memories for Layer: '{layer}' and Query: '{input_text}' ---")
    #         if final_layered_results[layer]:
    #             for i, chunk in enumerate(final_layered_results[layer]):
    #                 logger.info(f"   {i+1}. [ID: {chunk.id}, L:{chunk.layer_id}, S:{chunk.scene_id}, T:'{chunk.tag}'] Text: '{chunk.text[:40]}...'")
    #         else:
    #             logger.info(f"   No memories retrieved for layer '{layer}'.")

    #     return final_layered_results
    def retrieve_layered(self, input_text, desired_sub_storages, current_scene_id=None):
        sub_storage_query_list = []
        for sub_storage_name in desired_sub_storages:
            sub_storage_query_list.append(self.storage.all_sub_storages[sub_storage_name])
        # Perform independent retrieval for each relevant sub-storage
        all_results_combined = {}
        for sub_storage in sub_storage_query_list:
            logger.info(f"\n--- Retrieving from {type(sub_storage).__name__} ---")
            # Retrieve from sub-storage. It will apply its internal weights and return top_k
            # We ask for top_k * 2 to give some room for filtering/re-ranking later if needed
            sub_storage_results = sub_storage.retrieve(
                query_text=input_text, 
                current_scene_id=current_scene_id, 
                top_k=self.top_k, # Fetch more to allow for final filtering/re-ranking
                bm25_weight=self.bm25_weight, 
                vector_weight=self.vector_weight
            )
            
            # Since sub_storage.retrieve already returns a sorted list of {'score': score, 'chunk': chunk}
            # we just need to add them to a combined list
            sub_storage_results = sorted(sub_storage_results, key=lambda x: x['score'], reverse=True)
            all_results_combined.update({type(sub_storage).__name__: sub_storage_results})

        # Final filtering and grouping by desired_layers (within the originally requested layers)
        
        # Sort all combined results by score one last time
        # sorted_all_results = sorted(all_results_combined, key=lambda x: x['score'], reverse=True)

        return all_results_combined
# --- Example Usage ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    storage = MemoryStorage(chunk_max_pieces=5, chunk_overlap_pieces=2) 

    # Add initial chunks directly - they will be routed to GlobalMemorySubStorage
    storage.add_chunk("The ancient library holds forbidden knowledge.", "global", tag="scene_init", scene_id=1) # chunk_id 0 in Global
    storage.add_chunk("The hero must find the lost scroll to save the world.", "global", tag="scene_objective", scene_id=1) # chunk_id 1 in Global
    storage.add_chunk("The wizard's name is Elara and she is wise.", "global", tag="profile", scene_id=None) # chunk_id 2 in Global
    
    # Add conversation pieces incrementally - they will be routed to EventMemorySubStorage
    logger.info("\n--- Adding incremental conversation pieces for Scene 1 (Event Storage) ---")
    storage.add_piece("Hero: Hello, wise wizard!", "event", tag="conversation", scene_id=1) # piece 0, creates chunk 0 in Event
    storage.add_piece("Wizard: Greetings, young adventurer.", "event", tag="conversation", scene_id=1) # piece 1, adds to chunk 0 in Event
    storage.add_piece("Hero: I seek knowledge of the ancient scroll.", "event", tag="conversation", scene_id=1) # piece 2, adds to chunk 0 in Event
    storage.add_piece("Wizard: The scroll is hidden in the darkest depths.", "event", tag="conversation", scene_id=1) # piece 3, adds to chunk 0 in Event
    storage.add_piece("Hero: Tell me more about these depths.", "event", tag="conversation", scene_id=1) # piece 4, adds to chunk 0 in Event (now full: 5 pieces)

    logger.info("\n--- Adding 6th piece (triggering new chunk with overlap in Event Storage) ---")
    storage.add_piece("Wizard: Beware the guardians of the abyss.", "event", tag="conversation", scene_id=1) # piece 5, creates chunk 1 in Event
    
    logger.info("\n--- Adding 7th piece (appending to existing chunk in Event Storage) ---")
    storage.add_piece("Hero: Guardians? What kind of guardians?", "event", tag="conversation", scene_id=1) # piece 6, adds to chunk 1 in Event

    # Add an action piece - routed to EventMemorySubStorage
    storage.add_piece("The hero drew his sword, preparing for the abyss.", "event", tag="conversation", scene_id=1) # piece 7, creates chunk 2 in Event
    
    # Add some pieces for scene 2 - routed to EventMemorySubStorage
    logger.info("\n--- Adding incremental conversation pieces for Scene 2 (Event Storage) ---")
    storage.add_piece("Dragon: ROAR!", "event", tag="conversation", scene_id=2) # piece 8, creates chunk 3 in Event
    storage.add_piece("Knight: We must stand our ground!", "event", tag="conversation", scene_id=2) # piece 9, adds to chunk 3 in Event

    # Add a summary piece - routed to SummaryMemorySubStorage
    logger.info("\n--- Adding summary pieces (Summary Storage) ---")
    storage.add_chunk("The hero learned about the hidden scroll and abyss guardians.", "summary", tag="conversation", scene_id=1) # chunk 0 in Summary
    storage.add_chunk("Scene 1 begins with a quest for ancient knowledge.", "summary", tag="conversation", scene_id=1) # chunk 1 in Summary

    # Build BM25 for all sub-storages
    for sub_storage_name, sub_storage_obj in storage.all_sub_storages.items():
        sub_storage_obj.build_bm25()

    retriever = Retriever(storage, top_k=2, bm25_weight=0.5, vector_weight=0.5)

    print("\n" + "="*50)
    print("Retrieving memories for Query: 'tell me about the main character and recent dialogue'")
    print("="*50 + "\n")
    query_text = "tell me about the main character and recent dialogue"
    retrieved_memories = retriever.retrieve_layered(
        input_text=query_text, 
        current_scene_id=1,
        desired_sub_storages=["global", "event", "summary"]
    )

    print("\n" + "="*50)
    print("Final Retrieved Memories Grouped by Layer (from separate retrievals):")
    print("="*50 + "\n")
    for layer, chunks in retrieved_memories.items():
        print(f"--- Layer: {layer} ---")
        if chunks:
            for chunk in chunks:
                score = chunk['score']
                chunk = chunk['chunk']
                print(f"  Score: {score} [ID: {chunk.id}, L:{chunk.layer_id}, S:{chunk.scene_id}, T:'{chunk.tag}'] Text: '{chunk.text[:80]}...' (#pieces: {len(chunk.pieces)})")
        else:
            print("  No relevant memories found for this layer.")
        print("-" * 20)
    
    print("\n\n--- All Chunks in Storage for Inspection (across all sub-storages) ---")
    all_chunks_for_inspection = storage.all_chunks()
    for chunk in sorted(all_chunks_for_inspection, key=lambda x: x.id): # Sort by chunk_id for consistent output
        print(f"Chunk {chunk.id}: Layer='{chunk.layer}', Tag='{chunk.tag}', Scene={chunk.scene_id}, #Pieces={len(chunk.pieces)}, Text='{chunk.text[:100]}...'")