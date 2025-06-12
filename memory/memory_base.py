#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time 
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import faiss
from memory.document_processor import DocumentProcessor
from utils import get_keys
from utils import logger

# 假设层级定义和各层权重
LAYER_WEIGHTS = {
    "profile": 1.5,
    "scene_init": 1.3,
    "scene_objective": 1.4,
    "conversation": 1.0,
    "summary_conversation": 1.2, # Summaries might be slightly more important than raw convo
    "summary_scene_init": 1.1,
    "summary_scene_objective": 1.3,
    "archived_conversation": 0.2, # Low weight for archived items
    "archived_scene_init": 0.1,
    "archived_scene_objective": 0.1,
}
TAG_WEIGHT = 0.5
TEXT_WEIGHT = 0.5

TAG_WEIGHTS = {
    "profile": 1.5,
    "scene_init": 1.3,
    "scene_objective": 1.4,
    "conversation": 1.0,
    "summary_conversation": 1.2, # Summaries might be slightly more important than raw convo
}

# 定义MemoryChunk
class MemoryPiece:
    def __init__(self, piece_id, text="", layer="setting", metadata={}, layer_id=None, scene_id=None): # Added scene_id
        self.id = piece_id # unique id
        self.text = text # content
        self.layer = layer # setting, event_raw, event_summary
        self.metadata = metadata # tag: profile, scene_objective, conversation, etc.
        # self.timestamp = timestamp if timestamp is not None else time.time()
        self.layer_id = layer_id # Store layer_id
        self.embedding = None
        self.scene_id = scene_id # Store scene_id

    def __repr__(self):
        return f"MemoryPiece(id={self.id}, layer={self.layer}, layer_id = {self.layer_id}, scene_id={self.scene_id}, text={self.text})"

class MemoryChunk:
    def __init__(self, chunk_id, pieces=[], layer="setting", metadata={}, layer_id = None, scene_id=None, tag="conversation"): # Added scene_id
        self.id = chunk_id # unique id
        self.chunk = pieces # content        self.next_layer_id[layer] += 1        self.next_layer_id[layer] += 1
        self.piece_threshold = 1000  # Maximum number of pieces in a chunk
        self.text = " ".join([piece.text for piece in pieces]) # Concatenate text from all pieces
        self.layer = layer # setting, event_raw, event_summary
        self.metadata = metadata or {} # tag: profile, scene_objective, conversation, etc.
        self.layer_id = layer_id # Store layer_id
        self.embedding = None
        self.scene_id = scene_id # Store scene_id
        self.tag = tag # tag: profile, scene_objective, conversation, etc.
        self.tag_embedding = None

    def __repr__(self):
        return f"MemoryChunk(id={self.id}, layer={self.layer}, layer_id = {self.layer_id}, scene_id={self.scene_id}, text={self.text})"

    def add_piece(self, piece):
        if len(self.chunk) >= self.piece_threshold:
            logger.warning(f"Warning: Chunk {self.id} is full. Cannot add more pieces.")
            return False
        self.chunk.append(piece)
        self.text += " " + piece.text # Concatenate text from all pieces
        self.set_embedding(self.embed_model)
        return True

    def set_embedding(self, embed_model):
        text_embedding = embed_model.encode(self.text)
        combined_embedding = (TEXT_WEIGHT * text_embedding + TAG_WEIGHT * self.tag_embedding).astype('float32')
        self.embedding = combined_embedding

#   MemoryStorage：存储和索引构建
#   负责将每个记忆单元以 MemoryChunk 形式存储
#   同时维护两个索引：文本索引用于 BM25，向量索引用于语义匹配（faiss）。
#   每个记忆单元包含文本、层级信息、元数据及embedding向量。层级信息（profile, scene_init, scene_objective, conversation）可用于后续检索时的权重调整。
class MemoryStorage:
    def __init__(self, embed_model_name="all-MiniLM-L6-v2"):
        
        self.chunks = {}
        self.pieces = {"setting": [], "event_raw": [], "event_summary": []}
        self.next_id = 0
        self.next_layer_id = {"setting": 0, "event_raw": 0, "event_summary": 0}
        
        self.documents_for_bm25 = []  # List of tokenized texts for BM25
        self.chunk_ids_in_bm25_faiss_order = [] # Stores chunk_ids in the same order as documents_for_bm25 and FAISS vectors

        self.embed_model = SentenceTransformer(embed_model_name)
        self.dimension = self.embed_model.get_sentence_embedding_dimension()
        self.faiss_index = faiss.IndexFlatL2(self.dimension)
        self.bm25 = None
        self.tag_embeddings = {}
        self._preload_tag_embeddings()
        # OPTIMIZATION: Store dialogue IDs ordered per scene
        # { scene_id: [dialogue_chunk_id_A, dialogue_chunk_id_C, ...], ... }
        # self.scene_dialogues_ordered_ids = defaultdict(list)

    def _preload_tag_embeddings(self):
        logger.debug("Preloading layer embeddings...")
        for tag in get_keys(TAG_WEIGHTS):
            # Embed the layer name (e.g., "profile layer", "conversation layer")
            # Adding " layer" can sometimes help the model understand context
            self.tag_embeddings[tag] = self.embed_model.encode(tag).astype('float32')
        logger.debug("TAG embeddings preloaded.")

    def add_piece(self, text, layer, tag, metadata=None, scene_id=None, language="en"):
        piece = MemoryPiece(self.next_id, text, layer, tag, metadata, layer_id = self.next_layer_id[layer], scene_id=scene_id)
        self.pieces[layer].append(piece)

        if len(self.chunks) != 0:
            last_chunk_id = len(self.chunks)-1
            # add piece to the last chunks if they are not full
            while last_chunk_id >= 0:
                last_chunk = self.chunks[last_chunk_id]
                if last_chunk.layer == layer and last_chunk.scene_id == scene_id and last_chunk.tag == tag:
                    if self.chunks[last_chunk_id].add_piece(piece):
                        vec = np.array([self.chunks[last_chunk_id].embedding]).astype('float32')
                        self.faiss_index.remove_ids(np.array([last_chunk_id]))
                        self.faiss_index.add_with_ids(vec, np.array([last_chunk_id]))
                    else:
                        break
        self.add_chunk(text, layer, metadata, scene_id, language)
        self.next_layer_id[layer] += 1

    def add_chunk(self, text, layer, tag=None, metadata=None, scene_id=None, language="en"):
        chunk_id = self.next_id[layer]
        chunk = MemoryChunk(chunk_id, text, layer, tag, metadata, layer_id = self.next_layer_id, scene_id=scene_id)
        self.chunks[chunk_id] = chunk
        self.next_id += 1

        # Add to BM25 tracking lists
        tokenized_text = DocumentProcessor().tokenize_text(layer+":"+text)
        self.documents_for_bm25.append(tokenized_text)
        self.chunk_ids_in_bm25_faiss_order.append(chunk_id)

        # Calculate and add embedding to FAISS
        if chunk.tag:
            chunk.tag_embedding = self.tag_embeddings.get(chunk.tag)
            if chunk.tag_embedding is None:
                # Handle cases where chunk.layer is not in unique_layers (e.g., embed it on the fly or log a warning)
                logger.warning(f"Warning: Unexpected tag '{chunk.tag}'. Embedding on the fly.")
                chunk.tag_embedding = self.embed_model.encode(chunk.tag).astype('float32')

        chunk.set_embedding(self.embed_model)
        # update FAISS index
        vec = np.array([chunk.embedding]).astype('float32')
        self.faiss_index.add(vec)

    def build_bm25(self):
        if self.documents_for_bm25:
            self.bm25 = BM25Okapi(self.documents_for_bm25)
        else:
            self.bm25 = None # Or an empty BM25 object

    def update_indices(self):
        self.build_bm25()
        # FAISS is updated incrementally. If deletions are implemented, FAISS might need rebuilding or IndexIDMap.

    def get_chunk_by_bm25_faiss_internal_index(self, internal_idx):
        """Gets a chunk using its internal index from the BM25/FAISS ordered lists."""
        if 0 <= internal_idx < len(self.chunk_ids_in_bm25_faiss_order):
            chunk_id_to_fetch = self.chunk_ids_in_bm25_faiss_order[internal_idx]
            return self.chunks.get(chunk_id_to_fetch)
        return None
    
    def all_chunks(self): # For summarizer or other full traversals
        return list(self.chunks.values())

    def update_chunk_layer(self, chunk_id, new_layer): # From previous implementation
        if chunk_id in self.chunks:
            self.chunks[chunk_id].layer = new_layer
        else:
            logger.warning(f"Warning: Chunk ID {chunk_id} not found for layer update.")

    def update_chunk_properties(self, chunk_id, new_layer=None, new_tag=None):
        """
        Updates the layer and/or tag of an existing chunk, and rebuilds its embedding/index entry.
        Designed for use in archiving.
        """
        chunk = self.chunks.get(chunk_id)
        if not chunk:
            logger.warning(f"Chunk with ID {chunk_id} not found in {type(self).__name__} for update.")
            return False

        original_layer = chunk.layer
        original_tag = chunk.tag

        if new_layer:
            chunk.layer = new_layer
        if new_tag:
            chunk.tag = new_tag
        
        # Re-calculate embedding based on new layer/tag
        chunk.set_embedding(self.embed_model, self.tag_embeddings)

        # Update FAISS index (remove old, add new)
        # Note: FAISS doesn't have a direct "update" for embeddings. Remove + Add is the way.
        try:
            self.faiss_index.remove_ids(np.array([chunk_id]))
            vec = np.array([chunk.embedding]).astype('float32')
            self.faiss_index.add_with_ids(vec, np.array([chunk_id]))
            logger.debug(f"[{type(self).__name__}] FAISS entry updated for chunk {chunk_id}.")
        except Exception as e:
            logger.error(f"[{type(self).__name__}] Error updating FAISS for chunk {chunk_id}: {e}")
            return False

        # Update BM25 document text if layer/tag changed
        if new_layer or new_tag:
            bm25_internal_idx = self.chunk_id_to_bm25_internal_idx.get(chunk_id)
            if bm25_internal_idx is not None and bm25_internal_idx < len(self.documents_for_bm25):
                updated_bm25_doc_text = f"{chunk.layer}:{chunk.text}"
                self.documents_for_bm25[bm25_internal_idx] = DocumentProcessor().tokenize_text(updated_bm25_doc_text)
                self.build_bm25() # Rebuild BM25 after document change
                logger.debug(f"[{type(self).__name__}] BM25 document updated for chunk {chunk_id}. Rebuilding BM25.")
            else:
                logger.warning(f"[{type(self).__name__}] BM25 internal index for chunk {chunk_id} not found or out of bounds. BM25 may be inconsistent.")

        logger.info(f"[{type(self).__name__}] Chunk {chunk_id} updated: Layer {original_layer}->{chunk.layer}, Tag {original_tag}->{chunk.tag}.")
        return True
