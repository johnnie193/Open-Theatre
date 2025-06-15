from utils import logger
from utils import query_gpt4
import numpy as np
from memory.document_processor import DocumentProcessor

class Summarizer:
    def __init__(self, memory_storage, summary_chunk_size=5):
        self.memory_storage = memory_storage
        self.summary_chunk_size = summary_chunk_size # Number of original event chunks to summarize at once
        
    def _generate_summary_text(self, text_to_summarize):
        """Generates a summary for a given text using a GPT-4o model."""
        prompt = f"""
        Summarize the following text:
        {text_to_summarize}
        """
        return query_gpt4(prompt)

    def summarize_scene_events(self, scene_id, summary_tag="summary_conversation"):
        """
        Summarizes events for a given scene_id, stores them in summary_storage,
        and then MOVES the original chunks to archive_storage.
        
        Args:
            scene_id (int): The ID of the scene whose events are to be summarized.
            summary_tag (str): The tag to assign to the generated summary chunks.
        """
        logger.info(f"Attempting to summarize and move events for scene ID: {scene_id}")

        event_chunks_to_summarize = []
        for chunk_id, chunk in self.memory_storage.event_storage.chunks.items():
            # Only consider active conversation, action, thought chunks for summarization
            if chunk.scene_id == scene_id and \
               chunk.tag in ["conversation", "action", "thought"]:
                event_chunks_to_summarize.append(chunk)
        
        if not event_chunks_to_summarize:
            logger.info(f"No active event chunks found for scene ID: {scene_id}. Skipping summarization.")
            return

        # Sort chunks by their global ID to ensure chronological order
        event_chunks_to_summarize.sort(key=lambda c: c.id)

        chunks_to_move = [] # Collect chunks that were summarized and need moving

        # Group chunks by summary_chunk_size and generate summaries
        for i in range(0, len(event_chunks_to_summarize), self.summary_chunk_size):
            batch_of_chunks = event_chunks_to_summarize[i:i + self.summary_chunk_size]
            
            combined_text = "\n".join([c.text for c in batch_of_chunks])
            
            logger.debug(f"Summarizing batch of {len(batch_of_chunks)} chunks from scene {scene_id} (IDs: {[c.id for c in batch_of_chunks]})")
            
            summary_text = self._generate_summary_text(combined_text)
            
            # Add generated summary as a piece to the SummaryMemorySubStorage
            # The add_piece method will handle creating a new chunk in summary_storage
            self.memory_storage.add_piece(
                text=summary_text,
                layer="summary",
                tag=summary_tag,
                metadata={"source_scene_id": scene_id, "source_chunk_ids": [c.id for c in batch_of_chunks]},
                scene_id=scene_id 
            )
            logger.debug(f"Added summary piece for scene {scene_id}: {summary_text[:100]}...")

            # Collect chunks that were part of this summary batch for moving
            chunks_to_move.extend(batch_of_chunks)
        
        # --- Moving Original Chunks to Archive ---
        logger.info(f"Moving {len(chunks_to_move)} original chunks for scene {scene_id} to archive storage.")
        for original_chunk in chunks_to_move:
            # 1. Remove from EventMemorySubStorage
            removed_chunk = self.memory_storage.event_storage.remove_chunk(original_chunk.id)
            
            if removed_chunk:
                # 2. Update its layer and tag to 'archived_'
                archived_layer = f"archived_{removed_chunk.layer}"
                archived_tag = f"archived_{removed_chunk.tag}"

                # Ensure these new layers/tags are preloaded in the tag_embeddings
                if archived_layer not in self.memory_storage.tag_embeddings:
                    self.memory_storage.tag_embeddings[archived_layer] = \
                        self.memory_storage.embed_model.encode(archived_layer).astype('float32')
                if archived_tag not in self.memory_storage.tag_embeddings:
                    self.memory_storage.tag_embeddings[archived_tag] = \
                        self.memory_storage.embed_model.encode(archived_tag).astype('float32')

                removed_chunk.layer = archived_layer
                removed_chunk.tag = archived_tag
                removed_chunk.set_embedding(self.memory_storage.embed_model, self.memory_storage.tag_embeddings)
                
                # 3. Add to ArchiveMemorySubStorage
                # Note: We're directly adding the modified chunk object.
                # _create_and_add_new_chunk would create a brand new chunk with a new ID.
                # If we want to preserve the original chunk ID, we need to adapt _create_and_add_new_chunk
                # or have a specific method in ArchiveMemorySubStorage to add existing chunks.
                # For simplicity and preserving ID, we'll adapt BaseMemorySubStorage's internal add.
                
                # We need to manually add to archive_storage's internal dicts/indices
                # This bypasses the normal chunking logic of add_piece/add_chunk
                archive_storage = self.memory_storage.archive_storage
                archive_storage.chunks[removed_chunk.id] = removed_chunk

                bm25_doc_text = f"{removed_chunk.layer}:{removed_chunk.text}" 
                archive_storage.documents_for_bm25.append(DocumentProcessor().tokenize_text(bm25_doc_text))
                # Update the mapping for BM25 with the new index
                archive_storage.chunk_id_to_bm25_internal_idx[removed_chunk.id] = len(archive_storage.documents_for_bm25) - 1 

                vec = np.array([removed_chunk.embedding]).astype('float32')
                archive_storage.faiss_index.add_with_ids(vec, np.array([removed_chunk.id]))

                logger.info(f"Chunk {removed_chunk.id} (Layer: {original_chunk.layer}) moved to {removed_chunk.layer} in ArchiveStorage.")
            else:
                logger.warning(f"Failed to remove chunk {original_chunk.id} from EventMemorySubStorage during move operation.")

        # Rebuild BM25 for all affected storages after additions/removals/moves
        self.memory_storage.summary_storage.build_bm25()
        self.memory_storage.event_storage.build_bm25() # Event storage's BM25 needs to reflect removals
        self.memory_storage.archive_storage.build_bm25() # Archive storage's BM25 needs to reflect additions
        logger.info(f"Finished summarizing and moving events for scene ID: {scene_id}.")
