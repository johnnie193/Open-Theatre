from memory.memory_base import MemoryStorage, LAYER_WEIGHTS, TAG_WEIGHTS
import numpy as np
from utils import logger
from memory.document_processor import DocumentProcessor
BM25_WEIGHT = 0
VECTOR_WEIGHT = 1
TOP_K = 10

# MemoryRetriever：根据输入检索相关记忆，基于BM25和faiss两种方式融合结果‘
#   对新输入对话，先利用BM25基于关键词打分，再通过计算embedding向量与已有embedding的相似度，从faiss中快速检索。
#   两者按照预定权重（bm25_weight和vector_weight）融合，并进一步根据记忆层级的权重（LAYER_WEIGHTS）调节得分。
#   层级加权: 根据内存块的层级调整分数，允许优先检索。
class MemoryRetriever:
    def __init__(self, storage: MemoryStorage, bm25_weight=BM25_WEIGHT, vector_weight=VECTOR_WEIGHT, top_k=TOP_K):
        """
        bm25_weight和vector_weight指定两种方式在最终综合分数中的比例
        """
        self.storage = storage
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.top_k = top_k
    
    def retrieve(self, input_text, current_scene_id=None):
        tokenized_query = DocumentProcessor().tokenize_text(input_text)
        
        # Debug: Log the tokenized query
        logger.debug(f"Tokenized Query: {tokenized_query}")

        # Use FAISS to retrieve memories
        query_embedding = self.storage.embed_model.encode(input_text)
        vec = np.array([query_embedding]).astype('float32')
        
        # 确定faiss检索topk
        num_docs_in_faiss = self.storage.faiss_index.ntotal
        faiss_k = self.top_k * 3 
        if num_docs_in_faiss == 0:
            faiss_distances, faiss_indices = np.array([[]]), np.array([[]])
        else:
            actual_faiss_k = min(faiss_k, num_docs_in_faiss)
            faiss_distances, faiss_indices = self.storage.faiss_index.search(vec, actual_faiss_k)
        
        # 初始化向量得分
        vector_scores = np.zeros(len(self.storage.chunks))
        if faiss_indices.size > 0:
            valid_faiss_indices = faiss_indices[0][faiss_indices[0] < len(vector_scores)]
            valid_faiss_distances = faiss_distances[0][:len(valid_faiss_indices)]
            for dist, idx_in_faiss in zip(valid_faiss_distances, valid_faiss_indices):
                 vector_scores[idx_in_faiss] = 1.0 / (dist + 1e-9)

        combined_scores_with_info = []
        # Iterate based on the documents list used for BM25/FAISS, from back to front
        dialogue_turns_ago = 0
        for i in range(len(vector_scores)-1, -1, -1):
            if i >= len(vector_scores): continue # Should ideally not happen

            # Get the chunk object using its internal index in the BM25/FAISS ordered list
            base_score = vector_scores[i] 

            logger.debug(f"  Chunk ID: {chunk.id} | Layer: {chunk.layer} | Scene: {chunk.scene_id} | Text: '{chunk.text[:40]}...'")
            logger.debug(f"    Raw Vector Score: {base_score:.4f}")

            if base_score <= 1e-6: continue

            chunk = self.storage.chunks[i]
            tag_weight = TAG_WEIGHTS.get(chunk.layer, 1.0)
            score_with_layer = base_score * layer_weight

            logger.debug(f"    Layer Weight ({chunk.layer}): {layer_weight:.2f} -> Score after Layer Weight: {score_with_layer:.4f}")
            final_score = score_with_layer

            # Inter-scene recency
            if current_scene_id is not None and chunk.scene_id is not None:
                if chunk.layer != "setting" and chunk.tag != "profile":
                    scene_diff = abs(current_scene_id - chunk.scene_id)
                    inter_scene_recency_weight = 1.0 / (1 + 0.25 * scene_diff)
                    final_score *= inter_scene_recency_weight
                    logger.debug(f"    Inter-scene Recency Weight ({scene_diff}): {inter_scene_recency_weight:.2f} -> Score after Inter-scene Recency Weight: {final_score:.4f}")

            # Intra-scene recency FOR DIALOGUES (now using optimized pre-calculation)
            if current_scene_id is not None and \
               (chunk.layer == "conversation" or chunk.layer == "archived_conversation" or chunk.layer.startswith("summary_conversation")):
            #    chunk.scene_id == current_scene_id and \
                dialogue_turns_ago += 1
                K_dialogue_turn_recency = 0.005 
                intra_scene_dialogue_weight = 1.0 / (1 + K_dialogue_turn_recency * dialogue_turns_ago)
                final_score *= max(0.2, intra_scene_dialogue_weight)
                logger.debug(f"    Intra-Scene Recency (Turns ago: {dialogue_turns_ago}): {intra_scene_dialogue_weight:.4f}")
            
            logger.debug(f"    Final Score for Chunk {chunk.id}: {final_score:.4f}\n")
            if final_score > 1e-6:
                 combined_scores_with_info.append({'score': final_score, 'chunk': chunk})

        sorted_chunks_info = sorted(combined_scores_with_info, key=lambda x: x['score'], reverse=True)
        result_chunks = [info['chunk'] for info in sorted_chunks_info[:self.top_k]]

        logger.info(f"\n--- Top {self.top_k} Retrieved Memories for Query: '{input_text}' ---")
        if result_chunks:
            for i, chunk in enumerate(result_chunks):
                logger.info(f"  {i+1}. Layer: {chunk.layer} | Scene: {chunk.scene_id} | Text: '{chunk.text[:40]}...'")
        else:
            logger.info("  No memories retrieved.")
        return result_chunks

    def retrieve(self, input_text, current_scene_id=None):
        tokenized_query = DocumentProcessor().tokenize_text(input_text)
        
        # Debug: Log the tokenized query
        logger.debug(f"Tokenized Query: {tokenized_query}")

        if not self.storage.bm25 or not self.storage.documents_for_bm25:
            logger.warning("Warning: BM25 index not built or no documents. Returning empty list.")
            return []
        
        bm25_scores_all = self.storage.bm25.get_scores(tokenized_query)

        # Debug: Log BM25 scores
        logger.debug(f"BM25 Scores: {bm25_scores_all}")

        # Debug: Log document tokens
        for i, doc_tokens in enumerate(self.storage.documents_for_bm25):
            logger.debug(f"Document {i} Tokens: {doc_tokens}")

        # Check for common words between query and documents
        for i, doc_tokens in enumerate(self.storage.documents_for_bm25):
            common_words = set(tokenized_query).intersection(set(doc_tokens))
            logger.debug(f"Common words with Document {i}: {common_words}")

        query_embedding = self.storage.embed_model.encode(input_text)
        vec = np.array([query_embedding]).astype('float32')
        
        # 确定faiss检索topk
        num_docs_in_faiss = self.storage.faiss_index.ntotal
        faiss_k = self.top_k * 3 
        if num_docs_in_faiss == 0:
            faiss_distances, faiss_indices = np.array([[]]), np.array([[]])
        else:
            actual_faiss_k = min(faiss_k, num_docs_in_faiss)
            faiss_distances, faiss_indices = self.storage.faiss_index.search(vec, actual_faiss_k)
        
        # 初始化向量得分
        vector_scores = np.zeros(len(self.storage.documents_for_bm25))
        if faiss_indices.size > 0:
            valid_faiss_indices = faiss_indices[0][faiss_indices[0] < len(vector_scores)]
            valid_faiss_distances = faiss_distances[0][:len(valid_faiss_indices)]
            for dist, idx_in_faiss in zip(valid_faiss_distances, valid_faiss_indices):
                 vector_scores[idx_in_faiss] = 1.0 / (dist + 1e-9)

        combined_scores_with_info = []
        # Iterate based on the documents list used for BM25/FAISS, from back to front
        dialogue_turns_ago = 0
        for i in range(len(self.storage.documents_for_bm25)-1, -1, -1):
            if i >= len(bm25_scores_all): continue # Should ideally not happen

            # Get the chunk object using its internal index in the BM25/FAISS ordered list
            chunk = self.storage.get_chunk_by_bm25_faiss_internal_index(i)
            if not chunk:
                logger.warning(f"Warning: Could not retrieve chunk for document index {i}. Skipping.")
                continue

            bm25_s = bm25_scores_all[i]
            vector_s = vector_scores[i] 

            base_score = self.bm25_weight * bm25_s + self.vector_weight * vector_s
            logger.debug(f"  Chunk ID: {chunk.id} | Layer: {chunk.layer} | Scene: {chunk.scene_id} | Text: '{chunk.text[:40]}...'")
            logger.debug(f"    Raw BM25 Score: {bm25_s:.4f} | Raw Vector Score: {vector_s:.4f}")
            logger.debug(f"    Base Combined Score: {base_score:.4f} (BM25*{self.bm25_weight} + Vector*{self.vector_weight})")

            if base_score <= 1e-6: continue

            tag_weight = TAG_WEIGHTS.get(chunk.layer, 1.0)
            score_with_layer = base_score * tag_weight

            logger.debug(f"    Tag Weight ({chunk.tag}): {tag_weight:.2f} -> Score after Tag Weight: {score_with_layer:.4f}")
            final_score = score_with_layer

            # Inter-scene recency
            if current_scene_id is not None and chunk.scene_id is not None:
                if chunk.layer != "setting" and chunk.tag != "profile":
                    scene_diff = abs(current_scene_id - chunk.scene_id)
                    inter_scene_recency_weight = 1.0 / (1 + 0.25 * scene_diff)
                    final_score *= inter_scene_recency_weight
                    logger.debug(f"    Inter-scene Recency Weight ({scene_diff}): {inter_scene_recency_weight:.2f} -> Score after Inter-scene Recency Weight: {final_score:.4f}")

            # Intra-scene recency FOR DIALOGUES (now using optimized pre-calculation)
            if current_scene_id is not None and \
               (chunk.layer == "conversation" or chunk.layer == "archived_conversation" or chunk.layer.startswith("summary_conversation")):
            #    chunk.scene_id == current_scene_id and \
                dialogue_turns_ago += 1
                K_dialogue_turn_recency = 0.005 
                intra_scene_dialogue_weight = 1.0 / (1 + K_dialogue_turn_recency * dialogue_turns_ago)
                final_score *= max(0.2, intra_scene_dialogue_weight)
                logger.debug(f"    Intra-Scene Recency (Turns ago: {dialogue_turns_ago}): {intra_scene_dialogue_weight:.4f}")
            
            logger.debug(f"    Final Score for Chunk {chunk.id}: {final_score:.4f}\n")
            if final_score > 1e-6:
                 combined_scores_with_info.append({'score': final_score, 'chunk': chunk})

        sorted_chunks_info = sorted(combined_scores_with_info, key=lambda x: x['score'], reverse=True)
        result_chunks = [info['chunk'] for info in sorted_chunks_info[:self.top_k]]

        logger.info(f"\n--- Top {self.top_k} Retrieved Memories for Query: '{input_text}' ---")
        if result_chunks:
            for i, chunk in enumerate(result_chunks):
                logger.info(f"  {i+1}. Layer: {chunk.layer} | Scene: {chunk.scene_id} | Text: '{chunk.text[:40]}...'")
        else:
            logger.info("  No memories retrieved.")
        return result_chunks
