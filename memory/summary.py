from memory.memory_base import MemoryStorage, LAYER_WEIGHTS
from utils import query_gpt4

# Summarizer：定时对记忆数据进行总结更新
#   MemorySummarizer 模块定期对特定层级（如对话、场景目标、场景初始记忆）做总结归纳，产生摘要记忆。
#   层级归档: 在总结后归档原始内存块，以保持内存结构的清晰和高效
class MemorySummarizer:
    def __init__(self, storage: MemoryStorage, character_name="John"): # Added character_name
        self.storage = storage
        self.character_name = character_name
        # 假设使用外部大语言模型或者摘要模型
    
    def _get_conversation_summary_prompt(self, scene_id, dialogue_texts):
        dialogues_str = "\n".join([f"- \"{d}\"" for d in dialogue_texts])
        return (
            f"Character: {self.character_name}\n"
            f"Scene ID: {scene_id}\n\n"
            f"The following are dialogue entries for {self.character_name} in scene {scene_id}:\n"
            f"{dialogues_str}\n\n"
            f"Please provide a concise summary (1-2 sentences) of the key information revealed, "
            f"decisions made by {self.character_name}, and significant emotional shifts or relationship developments "
            f"for {self.character_name} based on these conversations. Focus on what would be important for {self.character_name} to remember moving forward."
        )
    
    def _get_default_summary_prompt(self, layer_to_summarize, scene_id_to_summarize, layer_events):
        events_str = "\n".join([f"- \"{e}\"" for e in layer_events])
        return (
            f"Character: {self.character_name}\nScene ID: {scene_id_to_summarize}\n"
            f"The following are entries for layer '{layer_to_summarize}':\n{events_str}\n\n"
            f"Please provide a concise summary (1-2 sentences) of the key takeaways."
        )

    def summarize_layer_for_scene(self, layer_to_summarize, scene_id_to_summarize, new_summary_layer_prefix="summary_"):
        chunks_to_summarize = [
            chunk for chunk in self.storage.all_chunks()
            if chunk.layer == layer_to_summarize and chunk.scene_id == scene_id_to_summarize
            and not chunk.metadata.get("is_summarized", False) # Don't re-summarize
        ]

        if not chunks_to_summarize:
            # print(f"No new chunks to summarize for layer '{layer_to_summarize}' in scene {scene_id_to_summarize}.")
            return None

        # Sort by timestamp to maintain order for the LLM
        chunks_to_summarize.sort(key=lambda x: x.timestamp)
        texts_for_summary = [chunk.text for chunk in chunks_to_summarize]

        if layer_to_summarize == "conversation":
            prompt = self._get_conversation_summary_prompt(scene_id_to_summarize, texts_for_summary)
        # Add other prompt generators for "scene_init", "scene_objective" if needed
        else:
            prompt = self._get_default_summary_prompt(layer_to_summarize, scene_id_to_summarize, texts_for_summary)

        summary_text = query_gpt4(prompt)

        if not summary_text:
            print(f"Failed to generate summary for layer '{layer_to_summarize}' in scene {scene_id_to_summarize}.")
            return None
        
        summary_metadata = {
            "source_layer": layer_to_summarize,
            "source_scene_id": scene_id_to_summarize,
            "original_chunk_ids": [chunk.id for chunk in chunks_to_summarize]
        }
        summary_chunk_layer = f"{new_summary_layer_prefix}{layer_to_summarize}"
        summary_chunk = self.storage.add_chunk(
            summary_text,
            layer=summary_chunk_layer,
            metadata=summary_metadata,
            scene_id=scene_id_to_summarize # Summary belongs to the same scene
        )
        print(f"Added summary: {summary_chunk}")

        # Archive original chunks
        archived_layer_name = f"archived_{layer_to_summarize}"
        for chunk in chunks_to_summarize:
            chunk.metadata["is_summarized"] = True
            chunk.metadata["summarized_by_id"] = summary_chunk.id
            # Option 1: Change layer (requires LAYER_WEIGHTS to have "archived_..." entries)
            self.storage.update_chunk_layer(chunk.id, archived_layer_name)
            # Option 2: Keep layer, just use metadata. Retriever must then check metadata.
            # Layer change is cleaner for weighting.

        return summary_chunk

    def periodic_summarize(self, completed_scene_id):
        """
        Summarizes specified layers for a recently completed scene.
        """
        print(f"\n=== Performing periodic summarization for completed scene {completed_scene_id} ===")
        summaries_added = {}
        layers_to_summarize_per_scene = ["conversation", "scene_objective"] # Example

        for layer in layers_to_summarize_per_scene:
            summary_chunk = self.summarize_layer_for_scene(layer, completed_scene_id)
            if summary_chunk:
                summaries_added[f"{layer}_scene_{completed_scene_id}"] = summary_chunk.text
        
        # if summaries_added:
        #     print("Rebuilding BM25 index after summarization...")
        #     self.storage.update_indices() # Crucial to rebuild BM25
        
        return summaries_added