# --- Main Memory Storage (Aggregator) ---
from memory.layers import GlobalMemorySubStorage, EventMemorySubStorage, SummaryMemorySubStorage, ArchiveMemorySubStorage
from memory.base import MemoryPiece
from collections import defaultdict
import logging
from sentence_transformers import SentenceTransformer
from utils import get_keys
from memory.base import TAG_WEIGHTS, LAYER_WEIGHTS
from memory.summarizer import Summarizer
from dotenv import load_dotenv, find_dotenv
import os   
load_dotenv(find_dotenv())
STORAGE_MODE = bool(os.getenv("STORAGE_MODE") and os.getenv("STORAGE_MODE").lower() in ["true", "1", "t", "y", "yes"])
# --- Setup Logging ---
logger = logging.getLogger(__name__)

class ModelSingleton:
    _instance = None

    @staticmethod
    def get_instance(embed_model_name="/data2/xuty/model/all-MiniLM-L6-v2"):
        if ModelSingleton._instance is None and STORAGE_MODE:
            ModelSingleton._instance = SentenceTransformer(embed_model_name)
        return ModelSingleton._instance

class MemoryStorage:
    def __init__(self, embed_model_name="/data2/xuty/model/all-MiniLM-L6-v2", chunk_max_pieces=5, chunk_overlap_pieces=1):
        self.embed_model = ModelSingleton.get_instance(embed_model_name)
        self.dimension = self.embed_model.get_sentence_embedding_dimension()
        self.tag_embeddings = {}
        self._preload_tag_embeddings()

        self.next_piece_id = 0
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
        self.retriever = Retriever(self)
        # self.tag_to_storage_map = {}
        # for storage_type, sub_storage in self.all_sub_storages.items():
        #     for tag in sub_storage.supported_tags:
        #         self.tag_to_storage_map[tag] = sub_storage

    def reset(self, chunk_max_pieces=5, chunk_overlap_pieces=1):
        logger.info("Resetting memory storage...")
        self.next_piece_id = 0
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

    def _get_next_global_chunk_id(self): # <--- NEW method
        new_id = self.next_global_chunk_id
        self.next_global_chunk_id += 1
        return new_id

    def _preload_tag_embeddings(self):
        # logger.info("Preloading tag embeddings...")
        # for tag in get_keys(TAG_WEIGHTS):
        #     self.tag_embeddings[tag] = self.embed_model.encode(tag).astype('float32')
        # logger.info("TAG embeddings preloaded.")
        
        
        pass
    
    def _get_sub_storage_for_layer(self, layer):
        
        return self.all_sub_storages[layer]

    def load_dialogues_record(self, dialogues_record, current_scene_id):
        '''
        输入参数：dialogues_record，一个dict，key是scene_id，value是list，list中每个元素是一个str，表示对话记录
        输出：None
        功能：将对话记录加载到memory中，每个对话记录作为一个piece，
        当前场景的对话记录添加到event_storage中，
        对其他场景的对话记录每个场景进行总结summary，将总结添加到summary_storage中，将其他场景的原始对话添加到archive_storage中
        '''
        logger.info(f"Loading dialogues record from empty memory storage...The current scene id is {current_scene_id}")
        for scene_id, dialogues in dialogues_record.items():
            if scene_id == current_scene_id:
                for dialogue in dialogues:
                    self.add_piece(dialogue, "event", tag="conversation", scene_id=scene_id)
            else:
                for dialogue in dialogues:
                    self.add_piece(dialogue, "event", tag="conversation", scene_id=scene_id)
                self.summarizer.summarize_scene_events(scene_id)

    def add_piece(self, text, layer, tag=None, metadata=None, scene_id=None):
        piece_id = self.next_piece_id
        self.next_piece_id += 1
        
        piece = MemoryPiece(piece_id, text, layer, tag, metadata, layer_id=None, scene_id=scene_id)
        
        sub_storage = self._get_sub_storage_for_layer(layer)
        added_piece = sub_storage.add_piece_to_sub_storage(piece)
        logger.info(f"Added piece {piece_id} to {layer} storage, the added piece is {added_piece}")
        return added_piece
    
    def delete_piece(self, piece_id, text=None):
        pass
    #TODO: Withdrawal is not available by delete_piece for memory storage now.

    def add_chunk(self, text, layer, tag=None, metadata=None, scene_id=None):
        piece_id = self.next_piece_id
        self.next_piece_id += 1
        
        single_piece = MemoryPiece(piece_id, text, layer, tag, metadata, layer_id=None, scene_id=scene_id)
        
        sub_storage = self._get_sub_storage_for_layer(layer)
        return sub_storage.add_chunk_to_sub_storage(single_piece)

    def all_chunks(self):
        """Returns all chunks from all sub-storages for inspection."""
        all_chunks = {}
        for sub_storage in self.all_sub_storages.values():
            all_chunks.update(sub_storage.chunks)
        return list(all_chunks.values())
    
    def all_chunks_values(self):
        """Returns all chunks from all sub-storages for inspection."""
        all_chunks = {}
        for sub_storage in self.all_sub_storages.values():
            all_chunks.update(sub_storage.chunks)
        return [chunk.state for chunk in list(all_chunks.values())]
    
    def get_chunk(self, chunk_id):
        """Attempts to get a chunk by ID from any sub-storage."""
        for sub_storage in self.all_sub_storages.values():
            chunk = sub_storage.get_chunk(chunk_id)
            if chunk:
                return chunk
        return None
    
    def retrieve(self, input_text: str, desired_sub_storages: list[str], current_scene_id=None):
        """
        Retrieve memories from multiple sub-storages.
        input_text: the query text
        desired_sub_storages: a list of sub-storage names to retrieve from
        current_scene_id: the current scene id

        Returns a list of {'score': score, 'chunk': chunk} dicts.
        """
        logger.info(f"Retrieving memories from memory storage...The current scene id is {current_scene_id}, the desired sub-storages are {desired_sub_storages}")
        return self.retriever.retrieve_layered(input_text, desired_sub_storages, current_scene_id)

    def summarize(self, scene_id, summary_tag="summary_conversation"):
        """
        Summarize memories from multiple sub-storages.
        """
        logger.info(f"Summarizing memories from memory storage...The scene id is {scene_id}")
        return self.summarizer.summarize_scene_events(scene_id, summary_tag=summary_tag)

# --- Retriever Class (modified to use sub-storages) ---
class Retriever:
    def __init__(self, storage, top_k=5, bm25_weight=0.3, vector_weight=0.5, importance_weight=0.2):
        self.storage = storage # This is now the main MemoryStorage aggregating sub-storages
        self.top_k = top_k
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.importance_weight = importance_weight

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
    def retrieve_layered(self, input_text: str, desired_sub_storages: list[str] = None, current_scene_id=None):
        """
        Retrieve memories from multiple sub-storages.
        input_text: the query text
        desired_sub_storages: a list of sub-storage names to retrieve from
        current_scene_id: the current scene id

        Returns a list of {'score': score, 'chunk': chunk} dicts.
        """
        sub_storage_query_list = []
        if not desired_sub_storages or not isinstance(desired_sub_storages, list):
            desired_sub_storages = ["event"]
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
                vector_weight=self.vector_weight,
                importance_weight=self.importance_weight
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
        print(type(all_chunks_for_inspection[0]))
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
        retriever = Retriever(storage, top_k=2, bm25_weight=0.4, vector_weight=0.5, importance_weight=0.1)
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

    def test():
        from utils import action_to_text
        storage = MemoryStorage(chunk_max_pieces=5, chunk_overlap_pieces=1)
                # scene.record.append(action_to_text(m))
        current_scene_id = "scene1"

        # Mouri comments on the sudden typhoon; the station master Kikuo and clerk Masako give everyone towels.
        m = {"a": "Mouri Kogoro", "x": "-speak", "b": "", "content": "Wow, it’s unbelievable that a typhoon would hit on the day we return to Tokyo."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Yuichi", "x": "-speak", "b": "Excited", "content": "I’m so excited to be here with the famous detective Kogoro Mouri!"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Kikuo", "x": "-speak", "b": "", "content": "Everyone, please bear with us. The weather forecast was totally wrong. Masako, please hand out towels to everyone."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Masako", "x": "-speak", "b": "Nervously", "content": "Ah... okay."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        # Hitoshi reflects on his failed life, and Yuichi seizes the opportunity to pitch his loans, leading to a confrontation.
        m = {"a": "Hitoshi", "x": "-speak", "b": "Sighs", "content": "Everything is like my life—just a series of sudden events and mistakes..."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Yuichi", "x": "-speak", "b": "", "content": "At times like this, we have a special offer for you. No way it will go wrong."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Hitoshi", "x": "-speak", "b": "Angrily grabs Yuichi by the collar", "content": "You scoundrel, how many people have you tricked with this nonsense?"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        # Yuichi’s briefcase falls, spilling many brochures. Morris offers help but is refused.
        m = {"a": "Yuichi", "x": "-speak", "b": "", "content": "I... I wasn’t trying to deceive anyone, just sharing better loan options. [Suddenly, the briefcase slips from Yuichi’s hand, spilling brochures on the floor—medical insurance...]"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Hitoshi", "x": "-speak", "b": "", "content": "This is exactly why my factory went bankrupt! No, I was forced into bankruptcy by the bank."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Yuichi", "x": "-speak", "b": "", "content": "Well, I’m not a bank! [Pushes Hitoshi away to pick up his things]"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Morris", "x": "-speak", "b": "Reaches out to help", "content": "Oh! Let me help you pick those up!"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Yuichi", "x": "-speak", "b": "Smiles and pushes Morris's hand away", "content": "I appreciate the gesture, but no need."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        # Kikuo informs everyone that trains have been suspended, and Noriko reveals her role as a politician’s secretary.
        m = {"a": "Mouri Kogoro", "x": "-speak", "b": "", "content": "... cough. When’s the next train? There must still be a train to Tokyo."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Kikuo", "x": "-speak", "b": "", "content": "I’m really sorry, we just received news that all trains have been canceled."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Mouri Kogoro", "x": "-speak", "b": "Surprised", "content": "What, really?!"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Noriko", "x": "-speak", "b": "Suddenly loud", "content": "This is ridiculous! If I miss my speech tomorrow, who’s going to take responsibility for it? The councilor is about to arrive at a nearby station."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Mouri Kogoro", "x": "-speak", "b": "", "content": "So, you must be... the secretary for councilor Sozaburo Tsujiwara."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        # Noriko complains that the councilor’s poster is too small, and Masako admits she wrote it.
        m = {"a": "Noriko", "x": "-speak", "b": "", "content": "I came early to prepare for tomorrow. By the way, who wrote that councilor’s poster? The name is too small; I need a new one."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Masako", "x": "-speak", "b": "Nervous", "content": "Ah... I wrote it. Okay."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        # Kikuo informs the group that the station’s phone line is down, and everyone must stay overnight.
        m = {"a": "Noriko", "x": "-speak", "b": "", "content": "And the phone here, can I use it?"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Kikuo", "x": "-speak", "b": "", "content": "Sorry, the phone lines are down due to the typhoon."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Yuichi", "x": "-speak", "b": "Suddenly excited", "content": "So we’re stuck here overnight... Isn't that great?!"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Noriko", "x": "-speak", "b": "", "content": "Stop joking!"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Mouri Kogoro", "x": "-speak", "b": "", "content": "Seems like things just keep getting worse..."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        # Kikuo suggests everyone use the station facilities, and Morris suggests they go to the hot springs.
        m = {"a": "Yuichi", "x": "-speak", "b": "", "content": "Oh, right... I’m hungry. Is there a restaurant here?"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Kikuo", "x": "-speak", "b": "", "content": "The station doesn’t have a restaurant. There are snacks at the gift shop; we’ll distribute some. Masako, go heat some water and prepare blankets for the ladies and children."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Masako", "x": "-speak", "b": "", "content": "Okay... okay."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Kikuo", "x": "-speak", "b": "", "content": "Wait a moment, I’ll go with you. Apologies, everyone; she’s still a newbie. By the way, the hot springs here are open to everyone while we wait for the trains to resume. I’ll be off now."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Morris", "x": "-speak", "b": "Excited", "content": "Anyone want to join me for a hot spring bath?"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        # query = "Can we use the phone in the typhoon?"
        # print(storage.retrieve(query, ["event"], "scene1"))

        # # --- Scene 2: Dangerous Warning ---
        current_scene_id = "scene2"

        # After the rain, the few people in the hot spring enjoy a brief moment of relaxation.
        m = {"a": "Morris", "x": "-speak", "b": "", "content": "The sound of the rain is still drizzling while we're soaking in the hot spring."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Mouri Kogoro", "x": "-speak", "b": "", "content": "It would be perfect if we could have some wine right now."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Yuichi", "x": "-speak", "b": "", "content": "That would be too indulgent."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Mouri Ran", "x": "-speak", "b": "", "content": "Conan, want to come over here? I can help you scrub your back."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        # Morris and Yuichi leave early, with Yuichi mentioning his concerns about his locker being unlocked.
        m = {"a": "Morris", "x": "-speak", "b": "", "content": "Sorry, I’ll get up first."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Yuichi", "x": "-speak", "b": "", "content": "In that case, I’ll get up too. The locker doesn’t have a lock, so poor travelers like me need to be extra careful."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Morris", "x": "-speak", "b": "Sweating profusely", "content": "What a bitter joke!"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        # Mouri Kogoro finds a note in the locker, which says—“Mr. Mouri, someone will be killed here tonight, the killer is...”.
        m = {"a": "Mouri Kogoro", "x": "-speak", "b": "", "content": "Huh, how did this note end up in my pocket?"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Conan", "x": "-speak", "b": "", "content": "Let me see, what’s written on it?"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Mouri Kogoro", "x": "-speak", "b": "Surprised", "content": "Mr. Mouri, someone will be killed here tonight, the killer is... what?!"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Conan", "x": "-speak", "b": "", "content": "Shh, if what’s written here is true, it will be dangerous if the criminal finds out."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Mouri Kogoro", "x": "-speak", "b": "", "content": "But don’t you think this is just a prank, with such a mysterious tone?"}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Conan", "x": "-speak", "b": "", "content": "They probably didn’t even have time to write the criminal’s name."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        # Mouri and Conan discuss who might have written the note, realizing that everyone is suspicious.
        m = {"a": "Mouri Kogoro", "x": "-speak", "b": "", "content": "So, who do you think wrote this note? I think it’s most likely one of those two who left the hot spring first."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        m = {"a": "Conan", "x": "-speak", "b": "", "content": "In my opinion, anyone in the waiting room could be the one."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        # Mouri Kogoro decides not to tell anyone about the note for now and suggests they investigate who wrote it.
        m = {"a": "Mouri Kogoro", "x": "-speak", "b": "After thinking for a moment", "content": "Conan, let’s not tell anyone about the note for now. Let’s first check what everyone was doing earlier."}
        storage.add_piece(action_to_text(m), layer="event", tag="conversation", scene_id=current_scene_id)

        query = "Can we use the phone in the typhoon?"
        print(storage.retrieve(query, ["event"], "scene2"))
                    
    test()