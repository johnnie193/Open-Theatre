from memory.base import BaseMemorySubStorage
from collections import defaultdict
import logging

# --- Setup Logging ---
logger = logging.getLogger(__name__)
IMPORTANCE_ADDITION_WEIGHT = 0.05
IMPORTANCE_ADDITION_THRESHOLD = 10
# --- Specific Sub-Storage Implementations ---
class GlobalMemorySubStorage(BaseMemorySubStorage):
    def __init__(self, parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces):
        super().__init__(parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces)
        self.supported_tags = ["profile", "scene_init", "scene_objective"]

    def retrieve(self, query_text, current_scene_id, top_k, bm25_weight, vector_weight, importance_weight):
        # Global memories don't have scene-specific recency, so pass None for current_scene_id to super
        final_retrieved_chunks = super().retrieve(query_text, None, top_k, bm25_weight, vector_weight, importance_weight)
        for chunk_info in final_retrieved_chunks:
            chunk = chunk_info['chunk']
            chunk.importance += min(chunk_info['score'], IMPORTANCE_ADDITION_THRESHOLD) * IMPORTANCE_ADDITION_WEIGHT # the retrieved chunks are more important
        return final_retrieved_chunks


class EventMemorySubStorage(BaseMemorySubStorage):
    def __init__(self, parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces):
        super().__init__(parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces)
        self.supported_tags = ["conversation", "action", "thought", "archived_conversation", "archived_scene_init", "archived_scene_objective"]
        self.scene_conversation_chunks = defaultdict(list) # Ordered list of conversation chunk IDs per scene

    def add_piece_to_sub_storage(self, piece):
        new_chunk_id = super().add_piece_to_sub_storage(piece)
        if new_chunk_id is not None and piece.layer == "conversation":
            self.scene_conversation_chunks[piece.scene_id].append(new_chunk_id)
        return new_chunk_id

    def add_chunk_to_sub_storage(self, piece):
        new_chunk_id = super().add_chunk_to_sub_storage(piece)
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

    def retrieve(self, query_text, current_scene_id, top_k, bm25_weight, vector_weight, importance_weight):
        raw_results = super().retrieve(query_text, current_scene_id, top_k * 2, bm25_weight, vector_weight, importance_weight) # Get more candidates
        
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
        final_results_sorted = sorted(final_results, key=lambda x: x['score'], reverse=True)[:top_k]


        for chunk_info in final_results_sorted:
            chunk = chunk_info['chunk']
            chunk.importance += min(chunk_info['score'], IMPORTANCE_ADDITION_THRESHOLD) * IMPORTANCE_ADDITION_WEIGHT # the retrieved chunks are more important
        return final_results_sorted

class SummaryMemorySubStorage(BaseMemorySubStorage):
    def __init__(self, parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces):
        super().__init__(parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces)
        self.supported_tags = ["summary_conversation", "summary_scene_init", "summary_scene_objective"]

    def retrieve(self, query_text, current_scene_id, top_k, bm25_weight, vector_weight, importance_weight):
        # Summary memories might also benefit from inter-scene recency if they are scene-specific
        raw_results = super().retrieve(query_text, current_scene_id, top_k * 2, bm25_weight, vector_weight, importance_weight)
        
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
        
        final_results_sorted = sorted(final_results, key=lambda x: x['score'], reverse=True)[:top_k]

        for chunk_info in final_results_sorted:
            chunk = chunk_info['chunk']
            chunk.importance += min(chunk_info['score'], IMPORTANCE_ADDITION_THRESHOLD) * IMPORTANCE_ADDITION_WEIGHT # the retrieved chunks are more important
        return final_results_sorted

class ArchiveMemorySubStorage(BaseMemorySubStorage):
    def __init__(self, parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces):
        super().__init__(parent_storage, embed_model, dimension, tag_embeddings, chunk_max_pieces, chunk_overlap_pieces)
        # These layers are where archived memories will reside
        self.supported_layers = [
            "archived_conversation", "archived_action", "archived_thought",
            "archived_scene_init", "archived_scene_objective" # If you ever archive these types
        ]
    
    def retrieve(self, query_text, current_scene_id, top_k, bm25_weight, vector_weight, importance_weight):
        # Archival memories typically have low recency, so a flat retrieval might be sufficient.
        # You could add a very low recency penalty here if needed for older archives.
        final_retrieved_chunks = super().retrieve(query_text, current_scene_id, top_k, bm25_weight, vector_weight, importance_weight)
        for chunk_info in final_retrieved_chunks:
            chunk = chunk_info['chunk']
            chunk.importance += min(chunk_info['score'], IMPORTANCE_ADDITION_THRESHOLD) * IMPORTANCE_ADDITION_WEIGHT # the retrieved chunks are more important
        return final_retrieved_chunks
