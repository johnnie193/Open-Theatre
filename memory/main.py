import time
from memory.memory_base import MemoryStorage
from memory.retriever import MemoryRetriever
from memory.summary import MemorySummarizer

def main():
    # 初始化内存存储
    storage = MemoryStorage()
    summarizer = MemorySummarizer(storage, character_name="John")
    retriever = MemoryRetriever(storage, top_k=10)

    print("--- Starting Complex RAG System Test ---")

    # --- Scene 1 Setup ---
    current_scene_id = 1
    print(f"\n### Scene {current_scene_id}: The Initial Investigation ###")

    # Profile: Core character traits
    storage.add_piece("John is a highly observant and analytical detective, always seeking the truth.", layer="setting", tag="profile")
    storage.add_piece("John has a strong moral compass and protects the innocent.", layer="setting", tag="profile")

    # Scene 1 Initial State & Objective
    storage.add_piece("The missing person, Sarah, was last seen near the old clock tower.", layer="setting", tag="scene_init", scene_id=current_scene_id)
    storage.add_piece("It's a stormy night, heavy rain and strong winds.", layer="event_raw", tag="scene_init", scene_id=current_scene_id)
    storage.add_piece("John's objective is to find Sarah and uncover any foul play.", layer="setting", tag="scene_objective", scene_id=current_scene_id)
    storage.add_piece("He must interview witnesses carefully to avoid panic.", layer="setting", tag="scene_objective", scene_id=current_scene_id)

    # Scene 1 Conversations (simulate turns)
    time.sleep(0.1)
    storage.add_piece("John asks witness: 'Did you notice anyone unusual around the clock tower?'", layer="event_raw", tag="conversation", scene_id=current_scene_id)
    time.sleep(0.1)
    storage.add_piece("Witness replies: 'Only a delivery truck, very late, unusual for this hour.'", layer="event_raw", tag="conversation", scene_id=current_scene_id)
    time.sleep(0.1)
    storage.add_piece("John thinks: 'A delivery truck... that's a new lead.'", layer="event_raw", tag="conversation", scene_id=current_scene_id)
    time.sleep(0.1)
    storage.add_piece("John to self: 'Must check security footage near the main road for that truck.'", layer="event_raw", tag="conversation", scene_id=current_scene_id)
    time.sleep(0.1)
    storage.add_piece("John considers: 'The witness seemed nervous, holding something back.'", layer="event_raw", tag="conversation", scene_id=current_scene_id)
    storage.update_indices() # Build BM25 after adding all initial chunks

    # --- Scene 1 Retrieval before summarization ---
    print(f"\n--- Retrieval during Scene {current_scene_id} ---")
    query_text_1 = "I need to remember what John's main goal is for Sarah."
    retrieved_chunks = retriever.retrieve(query_text_1, current_scene_id=current_scene_id)
    print(f"\nQuery: '{query_text_1}'")
    for i, chunk in enumerate(retrieved_chunks):
        print(f"  {i+1}. Layer: {chunk.layer}, Scene: {chunk.scene_id}, Text: '{chunk.text}'")
    assert any("Sarah" in c.text and c.layer == "scene_objective" for c in retrieved_chunks), "Should retrieve scene objective about Sarah."

    # query_text_2 = "What did the witness say about the clock tower?"
    # retrieved_chunks = retriever.retrieve(query_text_2, current_scene_id=current_scene_id)
    # print(f"\nQuery: '{query_text_2}'")
    # for i, chunk in enumerate(retrieved_chunks):
    #     print(f"  {i+1}. Layer: {chunk.layer}, Scene: {chunk.scene_id}, Text: '{chunk.text}'")
    # assert any("delivery truck" in c.text for c in retrieved_chunks), "Should retrieve conversation about delivery truck."

    # # # --- Scene 1 Summarization ---
    # print("\n--- Ending Scene 1 and Summarizing ---")
    # scene1_summaries = summarizer.periodic_summarize(completed_scene_id=current_scene_id)
    # print("\nScene 1 Summaries Generated:")
    # for key, summary_text in scene1_summaries.items():
    #     print(f"  {key}: '{summary_text}'")
    
    # print("\nAll chunks after Scene 1 Summarization (showing layer changes):")
    # for chk_id, chk_obj in storage.chunks.items():
    #     print(chk_obj)
    
    # # Assertions after summarization
    # assert any(c.layer == "summary_conversation" and c.scene_id == 1 for c in storage.all_chunks()), "Should have summary_conversation for Scene 1."
    # assert any(c.layer == "archived_conversation" and c.scene_id == 1 for c in storage.all_chunks()), "Original conversations should be archived."
    # assert any(c.layer == "summary_scene_objective" and c.scene_id == 1 for c in storage.all_chunks()), "Should have summary_scene_objective for Scene 1."


    # # # --- Scene 2 Setup ---
    # current_scene_id = 2
    # print(f"\n\n### Scene {current_scene_id}: The Docks Investigation ###")

    # storage.add_piece("John arrives at the old docks, a notorious place for illegal activities.", layer="scene_init", scene_id=current_scene_id)
    # storage.add_piece("His objective is to find the delivery truck and its driver, potentially a key suspect.", layer="scene_objective", scene_id=current_scene_id)
    # storage.add_piece("John must remain unseen; secrecy is crucial here.", layer="scene_objective", scene_id=current_scene_id)
    
    # # Scene 2 Conversations
    # time.sleep(0.1)
    # storage.add_piece("John whispers to himself: 'The air here smells of salt and decay.'", layer="conversation", scene_id=current_scene_id)
    # time.sleep(0.1)
    # storage.add_piece("He sees a large, rusty delivery truck by warehouse 7.", layer="conversation", scene_id=current_scene_id)
    # time.sleep(0.1)
    # storage.add_piece("John thinks: 'This could be the truck from the clock tower.'", layer="conversation", scene_id=current_scene_id)
    # time.sleep(0.1)
    # storage.add_piece("A shadowy figure emerges from the warehouse.", layer="conversation", scene_id=current_scene_id)
    # time.sleep(0.1)
    # storage.add_piece("John observes the figure: 'He looks familiar, where have I seen him?'", layer="conversation", scene_id=current_scene_id)
    # storage.update_indices()

    # --- Scene 2 Retrieval ---
    # print(f"\n--- Retrieval during Scene {current_scene_id} ---")
    # query_text_3 = "Who did John see at the docks, and what was familiar?"
    # retrieved_chunks = retriever.retrieve(query_text_3, current_scene_id=current_scene_id)
    # print(f"\nQuery: '{query_text_3}'")
    # for i, chunk in enumerate(retrieved_chunks):
    #     print(f"  {i+1}. Layer: {chunk.layer}, Scene: {chunk.scene_id}, Text: '{chunk.text}'")
    # assert any("familiar" in c.text for c in retrieved_chunks), "Should retrieve current scene conversation about familiar figure."
# TODO: 通过某一个chunk 增加上下chunk的权重或将上下文一起召回

    # --- Cross-Scene Retrieval: Current Scene 2 context, querying Scene 1 summary ---
    # print("\n--- Cross-Scene Retrieval: Querying with Scene 2 context for Scene 1 info ---")
    # query_text_4 = "What was the initial lead about a vehicle John found near the clock tower?" # This should hit scene 1 summary or archived
    # retrieved_chunks = retriever.retrieve(query_text_4, current_scene_id=current_scene_id)
    # print(f"\nQuery: '{query_text_4}'")
    # for i, chunk in enumerate(retrieved_chunks):
    #     print(f"  {i+1}. Layer: {chunk.layer}, Scene: {chunk.scene_id}, Text: '{chunk.text}'")
    # # This assertion is tricky with mock LLM as summary content is fixed. Better to check layer/scene.
    # assert any(c.layer in ["summary_conversation", "archived_conversation"] and c.scene_id == 1 for c in retrieved_chunks), "Should retrieve scene 1 info, potentially summarized."

    # # Query specifically for John's profile (should be highly weighted, not affected by scene_id recency)
    # query_text_5 = "What kind of person is John?"
    # retrieved_chunks = retriever.retrieve(query_text_5, current_scene_id=current_scene_id)
    # print(f"\nQuery: '{query_text_5}'")
    # for i, chunk in enumerate(retrieved_chunks):
    #     print(f"  {i+1}. Layer: {chunk.layer}, Scene: {chunk.scene_id}, Text: '{chunk.text}'")
    # assert any(c.layer == "profile" for c in retrieved_chunks), "Should retrieve profile chunks."

    # # Chinese language test
    # print("\n--- Testing Chinese Language Support ---")
    # storage.add_piece("约翰说: '这是非常重要的一条线索。'", layer="conversation", scene_id=current_scene_id, language="zh")
    # storage.add_piece("码头很黑，需要手电筒。", layer="scene_init", scene_id=current_scene_id, language="zh")
    # storage.update_indices()
    
    # query_text_cn = "约翰觉得什么线索很重要？"
    # retrieved_chunks_cn = retriever.retrieve(query_text_cn, current_scene_id=current_scene_id, language="zh")
    # print(f"\nQuery (Chinese): '{query_text_cn}'")
    # for i, chunk in enumerate(retrieved_chunks_cn):
    #     print(f"  {i+1}. Layer: {chunk.layer}, Scene: {chunk.scene_id}, Text: '{chunk.text}'")
    # assert any("线索" in c.text and c.layer == "conversation" for c in retrieved_chunks_cn), "Should retrieve Chinese conversation chunk."


    # # --- Scene 2 Summarization ---
    # print("\n--- Ending Scene 2 and Summarizing ---")
    # scene2_summaries = summarizer.periodic_summarize(completed_scene_id=current_scene_id)
    # print("\nScene 2 Summaries Generated:")
    # for key, summary_text in scene2_summaries.items():
    #     print(f"  {key}: '{summary_text}'")
    
    # print("\nAll chunks after Scene 2 Summarization:")
    # for chk_id, chk_obj in storage.chunks.items():
    #     print(chk_obj)
    
    # assert any(c.layer == "summary_conversation" and c.scene_id == 2 for c in storage.all_chunks()), "Should have summary_conversation for Scene 2."
    # assert any(c.layer == "archived_conversation" and c.scene_id == 2 for c in storage.all_chunks()), "Original conversations for Scene 2 should be archived."


    # # --- Final Cross-Scene Query after all summarizations ---
    # print("\n--- Final Retrieval: Querying across all summarized memories ---")
    # query_text_final = "What was the initial situation regarding Sarah's disappearance, and what clue about a vehicle did John find early on?"
    # retrieved_chunks_final = retriever.retrieve(query_text_final, current_scene_id=current_scene_id) # Still in context of scene 2 for recency
    # print(f"\nQuery: '{query_text_final}'")
    # # Expect to see a mix of profile, scene 1 summaries, and potentially scene 2 summaries/current conversations
    # for i, chunk in enumerate(retrieved_chunks_final):
    #     print(f"  {i+1}. Layer: {chunk.layer}, Scene: {chunk.scene_id}, Text: '{chunk.text}'")
    
    # # Assertions for final query
    # assert any(c.layer == "profile" for c in retrieved_chunks_final), "Profile should always be retrieved."
    # assert any(c.layer == "summary_scene_init" and c.scene_id == 1 for c in retrieved_chunks_final), "Should retrieve summary of Scene 1 init."
    # assert any(c.layer == "summary_conversation" and c.scene_id == 1 for c in retrieved_chunks_final), "Should retrieve summary of Scene 1 conversation."
    # assert any("truck" in c.text.lower() for c in retrieved_chunks_final), "Should retrieve information about the truck."


    print("\n--- Complex RAG System Test Complete ---")        
if __name__ == "__main__":
    main()