#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
from rank_bm25 import BM25Okapi
import faiss
from collections import defaultdict 
import logging
from memory.document_processor import DocumentProcessor
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
TAG_EMBEDDING_WEIGHT = 0.0 # current not used
TEXT_WEIGHT = 1.0

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
        self.text = "\n".join([p.text.strip() for p in pieces_list]) 
        self.layer = layer
        self.metadata = metadata or {}
        self.layer_id = layer_id
        self.embedding = None
        self.scene_id = scene_id
        self.tag = tag if tag else layer 
        self.tag_embedding = None
        self.importance = 0
        
        self.max_pieces = 5 
        self.max_text_length = 800 

    def __repr__(self):
        return f"MemoryChunk(id={self.id}, layer='{self.layer}', tag='{self.tag}', layer_id={self.layer_id}, scene_id={self.scene_id}, #pieces={len(self.pieces)}, text='{self.text[:50]}...')"

    @property
    def state(self):
        return f"MemoryChunk(id={self.id}, layer='{self.layer}', tag='{self.tag}', layer_id={self.layer_id}, scene_id={self.scene_id}, #pieces={len(self.pieces)}, text='{self.text}, metadata={self.metadata})"

    def add_piece(self, piece, embed_model, tag_embeddings, next_layer_id_for_piece):
        if len(self.pieces) > self.max_pieces or \
           len(self.text) + len(piece.text) + 1 > self.max_text_length: 
            logger.info(f"Chunk {self.id} is full (pieces:{len(self.pieces)}/{self.max_pieces}, len:{len(self.text)}/{self.max_text_length}). Cannot add piece {piece.id}.")
            return False
        piece.layer_id = next_layer_id_for_piece
        self.pieces.append(piece)
        self.text += "\n" + piece.text.strip() 
        self.set_embedding(embed_model, tag_embeddings) 
        logger.info(f"Added piece {piece.id} to chunk {self.id}. New text length: {len(self.text)}")
        return True

    def set_embedding(self, embed_model, tag_embeddings):
        # text_embedding = embed_model.encode(self.text).astype('float32')
        
        # if self.tag not in tag_embeddings:
        #     logger.warning(f"Tag '{self.tag}' not preloaded. Encoding on the fly.")
        #     tag_embeddings[self.tag] = embed_model.encode(self.tag).astype('float32')
        
        # self.tag_embedding = tag_embeddings[self.tag]
        
        # self.embedding = (TEXT_WEIGHT * text_embedding + TAG_EMBEDDING_WEIGHT * self.tag_embedding).astype('float32')
        self.embedding = embed_model.encode(self.text).astype('float32')

    def to_text(self):
        # character's profile/conversation memory in a scene
        if "character" in self.metadata:
            scene_id = self.scene_id if self.scene_id else "global"
            return f"""
    {self.metadata["character"]}'s {self.tag} memory chunk in {scene_id}.
    {self.text}
            """
        # event conversation memory
        else:
            scene_id = self.scene_id if self.scene_id else "global"
            return f"""
    This is a {self.tag} memory chunk in {scene_id}.
    {self.text}
            """

# --- Base Memory Sub-Storage Class ---
class BaseMemorySubStorage:
    def __init__(self, parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces):
        self.parent_storage = parent_storage
        self.chunks = {}  # {chunk_id: MemoryChunk object}
        self.all_pieces_ordered = [] # Only for overlap logic within this sub-storage
        self.next_chunk_id_in_layer = 0
        
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

    

    def _create_and_add_new_chunk(self, pieces_list, layer, tag, metadata, scene_id, piece_id_for_logging, layer_id):
        chunk_id = self.parent_storage._get_next_global_chunk_id()

        chunk = MemoryChunk(chunk_id, pieces_list=pieces_list, layer=layer, tag=tag, 
                            metadata=metadata, layer_id=layer_id, scene_id=scene_id)
        
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

    def add_piece_to_sub_storage(self, piece):
        """Adds a piece to this sub-storage, handling chunking and overlap."""
        # Update piece's layer_id before storing globally
        
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
            if most_recent_suitable_chunk.add_piece(piece, self.embed_model, self.tag_embeddings, self.next_chunk_id_in_layer):
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
                piece_id_for_logging=piece.id, layer_id=self.next_chunk_id_in_layer
            )
            self.next_chunk_id_in_layer += 1
            return new_chunk.id # Return the ID of the newly created chunk
        return None # Indicate no new chunk was created

    def add_chunk_to_sub_storage(self, piece):
        """Directly adds a new chunk with no overlap from previous chunks."""
        piece.layer_id = self.next_chunk_id_in_layer # Update piece's layer_id
        self.all_pieces_ordered.append(piece) # Still add to global list for consistency
        
        chunk = self._create_and_add_new_chunk(
            pieces_list=[piece], 
            layer=piece.layer, tag=piece.tag, metadata=piece.metadata, scene_id=piece.scene_id,
            piece_id_for_logging=piece.id, layer_id=self.next_chunk_id_in_layer
        )
        self.next_chunk_id_in_layer += 1
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

    def retrieve(self, query_text, current_scene_id, top_k, bm25_weight, vector_weight, importance_weight):
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

            base_score = (bm25_weight * bm25_s) + (vector_weight * vector_s) + (importance_weight * chunk.importance)
            
            if base_score <= 1e-6: 
                continue

            # Apply layer/tag specific weights
            layer_weight = LAYER_WEIGHTS.get(chunk.layer, 1.0) * TAG_WEIGHTS.get(chunk.tag, 1.0)
            final_score = base_score * layer_weight

            if current_scene_id is not None and chunk.scene_id is not None and chunk.scene_id != current_scene_id:
                try:
                    scene_diff = abs(current_scene_id - chunk.scene_id)
                except:
                    scene_diff = int(current_scene_id.split("scene")[1]) - int(chunk.scene_id.split("scene")[1])
                inter_scene_recency_weight = 1.0 / (1 + 0.25 * scene_diff)
                final_score *= inter_scene_recency_weight
                logger.info(f"  [{type(self).__name__}] Inter-scene Recency (diff {scene_diff}): {inter_scene_recency_weight:.2f} -> Score: {final_score:.4f}")

            scored_chunks_info.append({'score': final_score, 'chunk': chunk})
        
        # Sort and return top_k
        sorted_by_score = sorted(scored_chunks_info, key=lambda x: x['score'], reverse=True)
        final_retrieved_chunks = sorted_by_score[:top_k]
        return final_retrieved_chunks
    
    def remove_chunk(self, chunk_id):
        """
        Removes a chunk completely from this sub-storage, including its FAISS and BM25 entries.
        Returns the removed chunk object if successful, None otherwise.
        """
        chunk_to_remove = self.chunks.pop(chunk_id, None)
        if not chunk_to_remove:
            logger.warning(f"Chunk with ID {chunk_id} not found in {type(self).__name__} for removal.")
            return None

        # Remove from FAISS index
        try:
            self.faiss_index.remove_ids(np.array([chunk_id]))
            logger.debug(f"[{type(self).__name__}] FAISS entry removed for chunk {chunk_id}.")
        except Exception as e:
            logger.error(f"[{type(self).__name__}] Error removing FAISS entry for chunk {chunk_id}: {e}")
            # Continue even if FAISS removal fails, as chunk is already popped from self.chunks

        # Remove from BM25 related structures
        bm25_internal_idx = self.chunk_id_to_bm25_internal_idx.pop(chunk_id, None)
        if bm25_internal_idx is not None and bm25_internal_idx < len(self.documents_for_bm25):
            # Remove the document from the list. This will shift subsequent indices.
            self.documents_for_bm25.pop(bm25_internal_idx)
            # Rebuild the chunk_id_to_bm25_internal_idx map because indices have shifted
            self.chunk_id_to_bm25_internal_idx = {}
            for i, doc_tokens in enumerate(self.documents_for_bm25):
                # This assumes chunk_id can be extracted from doc_tokens or that BM25 internal order
                # directly maps to how we populate. A more robust way is to store chunk_id with doc.
                # For simplicity here, we assume re-mapping all after a pop.
                # A better approach would be to store a list of (chunk_id, tokenized_doc)
                # and rebuild from that list.
                # For now, we'll iterate through existing chunks to rebuild.
                pass # Will rebuild completely below
            
            # Rebuild BM25 map based on remaining chunks in self.chunks
            self.chunk_id_to_bm25_internal_idx = {}
            temp_docs = []
            for i, c_id in enumerate(sorted(self.chunks.keys())): # Iterate sorted keys to keep some order
                chunk = self.chunks[c_id]
                temp_docs.append(DocumentProcessor().tokenize_text(f"{chunk.layer}:{chunk.text}"))
                self.chunk_id_to_bm25_internal_idx[c_id] = i
            self.documents_for_bm25 = temp_docs # Update the document list
            self.build_bm25() # Rebuild BM25 index after document change
            logger.debug(f"[{type(self).__name__}] BM25 document and index rebuilt after removing chunk {chunk_id}.")
        else:
            logger.warning(f"[{type(self).__name__}] BM25 internal index for chunk {chunk_id} not found or out of bounds. BM25 may be inconsistent or not need rebuild for this removal.")

        # Remove from all_pieces_ordered
        # This is tricky as all_pieces_ordered maintains a chronological list of ALL pieces,
        # not just ones currently in chunks. If a chunk is removed, its pieces are still in all_pieces_ordered.
        # For a true "remove" from the *sub-storage's perspective*, you might also want to remove pieces.
        # However, for the purpose of overlap, it might be fine to leave them, or you could implement
        # a more complex piece tracking. For now, we'll keep it simple and not remove individual pieces from all_pieces_ordered.
        # This means all_pieces_ordered will still contain pieces from removed chunks.
        # If this causes issues for overlap logic or memory, a more sophisticated solution is needed.
        
        logger.info(f"[{type(self).__name__}] Chunk {chunk_id} completely removed.")
        return chunk_to_remove