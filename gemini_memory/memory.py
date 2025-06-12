# --- Main Memory Storage (Aggregator) ---
from gemini_memory.layers import GlobalMemorySubStorage, EventMemorySubStorage, SummaryMemorySubStorage, ArchiveMemorySubStorage
from gemini_memory.base import MemoryPiece
from collections import defaultdict
import logging
from sentence_transformers import SentenceTransformer
from utils import get_keys
from gemini_memory.base import TAG_WEIGHTS, LAYER_WEIGHTS
from gemini_memory.summarizer import Summarizer

# --- Setup Logging ---
logger = logging.getLogger(__name__)

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
        self.archive_storage = ArchiveMemorySubStorage(self, self.embed_model, self.dimension, self.tag_embeddings, chunk_max_pieces, chunk_overlap_pieces) # NEW Archive Storage

        self.all_sub_storages = {
            "global": self.global_storage,
            "event": self.event_storage,
            "summary": self.summary_storage,
            "archive": self.archive_storage
        }

        self.summarizer = Summarizer(self)
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
    # Initialize logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    def test_1():
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


    def test_2():
        storage = MemoryStorage(chunk_max_pieces=5, chunk_overlap_pieces=2) 

        # Add initial chunks directly - they will be routed to GlobalMemorySubStorage
        storage.add_chunk("The ancient library holds forbidden knowledge.", "global", tag="scene_init", scene_id=1) 
        storage.add_chunk("The hero must find the lost scroll to save the world.", "global", tag="scene_objective", scene_id=1) 
        storage.add_chunk("The wizard's name is Elara and she is wise.", "global", tag="profile", scene_id=None) 
        
        # Add conversation pieces incrementally for Scene 1 (Event Storage)
        logger.info("\n--- Adding incremental conversation pieces for Scene 1 (Event Storage) ---")
        storage.add_piece("Hero: Hello, wise wizard!", "event", tag="conversation", scene_id=1) 
        storage.add_piece("Wizard: Greetings, young adventurer.", "event", tag="conversation", scene_id=1) 
        storage.add_piece("Hero: I seek knowledge of the ancient scroll.", "event", tag="conversation", scene_id=1) 
        storage.add_piece("Wizard: The scroll is hidden in the darkest depths.", "event", tag="conversation", scene_id=1) 
        storage.add_piece("Hero: Tell me more about these depths.", "event", tag="conversation", scene_id=1) 
        storage.add_piece("Wizard: Beware the guardians of the abyss.", "event", tag="conversation", scene_id=1) # Triggers new chunk
        storage.add_piece("Hero: Guardians? What kind of guardians?", "event", tag="conversation", scene_id=1) 
        storage.add_piece("Wizard: They are ancient, powerful, and many.", "event", tag="conversation", scene_id=1)

        # Add an action piece - routed to EventMemorySubStorage
        storage.add_piece("The hero drew his sword, preparing for the abyss.", "event", tag="action", scene_id=1) 
        
        # Add some pieces for scene 2 - routed to EventMemorySubStorage
        logger.info("\n--- Adding incremental conversation pieces for Scene 2 (Event Storage) ---")
        storage.add_piece("Dragon: ROAR!", "event", tag="conversation", scene_id=2) 
        storage.add_piece("Knight: We must stand our ground!", "event", tag="conversation", scene_id=2) 
        storage.add_piece("Princess: I believe in you, brave knight!", "event", tag="conversation", scene_id=2)

        # Build BM25 for all sub-storages (initial build)
        for sub_storage_name, sub_storage_obj in storage.all_sub_storages.items():
            sub_storage_obj.build_bm25()

        # --- Simulate Scene 1 ending and summarizing its events ---
        print("\n" + "="*50)
        print("SIMULATING SCENE 1 END & SUMMARIZING AND ARCHIVING EVENTS")
        print("="*50 + "\n")
        
        # Call summarizer for scene 1
        storage.summarizer.summarize_scene_events(scene_id=1) 
        
        print("\n" + "="*50)
        print("Retrieving memories for Query: 'what happened in the last scene'")
        print("Note: Original conversation chunks should now be archived.")
        print("="*50 + "\n")
        retriever = Retriever(storage, top_k=2, bm25_weight=0.5, vector_weight=0.5)
        query_text = "what happened in the last scene"
        retrieved_memories = retriever.retrieve_layered(
            input_text=query_text, 
            current_scene_id=1, # Still in scene 1 context for query
            desired_sub_storages=["global", "event", "summary", "archive"]
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
                    print(f"  Score: {score} [ID: {chunk.id}, L:{chunk.layer}, S:{chunk.scene_id}, T:'{chunk.tag}'] Text: '{chunk.text[:80]}...' (#pieces: {len(chunk.pieces)})")
            else:
                print("  No relevant memories found for this layer.")
            print("-" * 20)
        
        print("\n\n--- All Chunks in Storage for Inspection (across all sub-storages, after summarization/archiving) ---")
        all_chunks_for_inspection = storage.all_chunks()
        for chunk in sorted(all_chunks_for_inspection, key=lambda x: x.id): 
            print(f"Chunk {chunk.id}: Layer='{chunk.layer}', Tag='{chunk.tag}', Scene={chunk.scene_id}, #Pieces={len(chunk.pieces)}, Text='{chunk.text[:100]}...'")

    test_2()
