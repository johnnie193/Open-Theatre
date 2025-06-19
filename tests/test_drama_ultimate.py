# tests/test_drama_ultimate.py

import pytest
import asyncio
from fastapi.testclient import TestClient
import json
import os
import datetime
import yaml
import logging

# 从您的主应用文件中导入 app, DRAMA 类, 和 get_dramaworld 依赖
from main import app, DRAMA, get_dramaworld, LoadRequest, InteractRequest, InfoRequest, ScriptData, CharacterRequest, SceneRequest

# --- 配置 ---
REPORTS_DIR = "test_reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

DIALOGUE_INPUTS = [
    {
        "type": "-speak",
        "object": "Mouri Ran",
        "message": "Ran sister, we really have to stay here overnight? I'm afraid of thunder."
    },
    {
        "type": "-stay"
    },
    {
        "type": "-speak",
        "object": "Mouri Kogoro",
        "message": "Kogoro uncle, when could we leave."
    },
    {
        "type": "-stay"
    },
    {
        "type": "-speak",
        "object": "Masako",
        "message": "The big sister, your hands are shaking, is it because the wind is too strong and you feel cold?"
    },
    {
        "type": "-stay"
    },
    {
        "type": "-speak",
        "object": "Mouri Ran",
        "message": "Ran sister, look, the auntie called Noriko is always looking at her phone, as if she's in a hurry."
    },
    {
        "type": "-speak",
        "object": "Kikuo",
        "message": "Station master uncle, since the phone line is broken, are we completely cut off from the outside world?"
    },
]

# --- 辅助函数 ---
def transform_from_state_response(initial_state: dict) -> dict:
    """
    将从 /api/data 获取的完整状态（state）转换为符合 ScriptData 模型的 payload。
    这是为了调用 POST /api/data 接口来重新加载和初始化 dramaworld。
    """
    transformed_characters = []
    if "characters" in initial_state and initial_state["characters"]:
        for cid, char_info in initial_state["characters"].items():
            initial_mem = ""
            # initial_memory 在 dramaworld.script["background"]["context"] 中
            if "script" in initial_state and "background" in initial_state["script"] and \
               "context" in initial_state["script"]["background"] and initial_state["script"]["background"]["context"] and cid in initial_state["script"]["background"]["context"]:
                initial_mem = initial_state["script"]["background"]["context"][cid]
            transformed_characters.append(CharacterRequest(
                id=cid,
                profile=char_info.get("profile"),
                initial_memory=initial_mem
            ).model_dump(exclude_unset=True))

    transformed_scenes = {}
    if "scenes" in initial_state and initial_state["scenes"]:
        for sid, scene_info in initial_state["scenes"].items():
            script_scene_details = initial_state.get("script", {}).get("scenes", {}).get(sid, {})
            transformed_scenes[sid] = SceneRequest(
                sceneName=scene_info.get("name"),
                sceneInfo=scene_info.get("info"),
                mode=scene_info.get("mode"),
                characters=list(scene_info["characters"].keys()) if "characters" in scene_info else [],
                chains=script_scene_details.get("chain", []),
                streams=script_scene_details.get("stream", {})
            ).model_dump(exclude_unset=True)

    return ScriptData(
        id=initial_state.get("id"),
        player_name=initial_state.get("player_name"),
        background_narrative=initial_state.get("background_narrative"),
        characters=transformed_characters,
        scenes=transformed_scenes,
        storageMode=initial_state.get("storageMode", True)
    ).model_dump(exclude_unset=True)


# --- Pytest 测试用例 ---

@pytest.mark.asyncio
async def test_e2e_drama_flow():
    """
    端到端测试，对比V1/V2模式及不同storage_mode下的多轮对话响应。
    并输出每轮的详细数据。
    """
    scenarios = [
        {"script_name": "load-script-station", "drama_mode": "v2", "storage_mode": True},
        {"script_name": "load-script-station", "drama_mode": "v2", "storage_mode": False},
        {"script_name": "load-script-station", "drama_mode": "v1", "storage_mode": True},
        {"script_name": "load-script-station", "drama_mode": "v1", "storage_mode": False},
    ]

    scenario_test_env = {} 

    print("\n" + "="*80)
    print("                 [终极 DRAMALLM 端到端测试]                  ")
    print("="*80 + "\n")

    # 1. 初始化所有场景的独立 DRAMA 实例并加载剧本
    print("\n--- [阶段一: 初始化所有测试场景的独立环境] ---")
    
    for scenario in scenarios:
        scenario_key = f"mode_{scenario['drama_mode']}_storage_{scenario['storage_mode']}"
        print(f"\n🚀 正在设置场景: {scenario_key}...")
        
        # Create a new, independent DRAMA instance for this scenario
        independent_dramaworld_for_scenario = DRAMA()
        
        # Override the dependency for this specific test client
        # This makes the TestClient use our independent DRAMA instance
        app.dependency_overrides[get_dramaworld] = lambda: independent_dramaworld_for_scenario
        
        client = TestClient(app) 

        try:
            # Load the script using the client (which now uses our independent instance)
            load_response = client.post("/api/load", json={"script_name": scenario["script_name"], "storageMode": scenario["storage_mode"]})
            assert load_response.status_code == 200, f"[{scenario_key}] 加载剧本失败: {load_response.text}"
            initial_state = load_response.json()

            current_scene_id = "scene" + str(initial_state.get("scene_cnt", 1))

            # If the loaded script's current scene mode doesn't match the target mode, update it
            if initial_state.get("scenes", {}).get(current_scene_id, {}).get("mode") != scenario["drama_mode"]:
                print(f"    -> 模式不匹配（{initial_state.get('scenes', {}).get(current_scene_id, {}).get('mode')} != {scenario['drama_mode']}），正在更新...")
                
                # Update state dictionary directly (will be transformed by transform_from_state_response)
                initial_state["scenes"][current_scene_id]["mode"] = scenario["drama_mode"]
                
                # Use helper function to convert current state to ScriptData payload
                payload_for_update = transform_from_state_response(initial_state=initial_state)
                # Ensure storageMode is explicitly set in payload if needed by API
                payload_for_update["storageMode"] = scenario["storage_mode"] 

                update_response = client.post("/api/data", json=payload_for_update)
                assert update_response.status_code == 200, f"[{scenario_key}] 更新模式失败: {update_response.text}"
                print(f"    ✅ 模式已成功更新为 '{scenario['drama_mode']}'。")
                
                # Re-fetch updated state to verify
                re_verify_state_response = client.get("/api/data")
                assert re_verify_state_response.status_code == 200, f"[{scenario_key}] 重新获取状态失败: {re_verify_state_response.text}"
                re_verify_state = re_verify_state_response.json()
                assert re_verify_state["scenes"][current_scene_id]["mode"] == scenario["drama_mode"], \
                    f"[{scenario_key}] 更新模式后验证失败。预期: {scenario['drama_mode']}, 实际: {re_verify_state['scenes'][current_scene_id]['mode']}"
                print(f"    ✅ 重新验证模式成功。")

            # Verify the mode and storage mode of the independent DRAMA instance
            assert independent_dramaworld_for_scenario.dramallm.mode == scenario["drama_mode"], \
                f"[{scenario_key}] DRAMALLM 模式不匹配。预期: {scenario['drama_mode']}, 实际: {independent_dramaworld_for_scenario.dramallm.mode}"
            assert independent_dramaworld_for_scenario.dramallm.storage_mode == scenario["storage_mode"], \
                f"[{scenario_key}] DRAMALLM 存储模式不匹配。预期: {scenario['storage_mode']}, 实际: {independent_dramaworld_for_scenario.dramallm.storage_mode}"
            
            scenario_test_env[scenario_key] = {
                "client": client,
                "drama_instance": independent_dramaworld_for_scenario
            }
            print(f"✅ 场景 '{scenario_key}' 设置完毕。")

        except AssertionError as e:
            print(f"❌ 场景 '{scenario_key}' 设置失败: {e}")
            raise 
        except Exception as e:
            print(f"❌ 场景 '{scenario_key}' 设置时发生意外错误: {e}")
            import traceback
            print(traceback.format_exc())
            raise
        finally:
            # Clean up dependency override after each scenario setup
            app.dependency_overrides = {} 

    # 2. 按顺序执行每一轮对话，并收集所有场景的响应及状态
    print("\n--- [阶段二: 逐轮执行对话并对比响应和状态] ---")
    full_report = {
        "test_run_timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "dialogue_rounds": []
    }

    for i, user_input in enumerate(DIALOGUE_INPUTS):
        print(f"\n--- [对话轮次 {i+1}/{len(DIALOGUE_INPUTS)}] ---")
        print(f"▶️ 玩家输入: {json.dumps(user_input, ensure_ascii=False)}")

        turn_data = {
            "turn_number": i + 1,
            "user_input": user_input,
            "scenario_outputs": {}
        }

        for scenario_key, env in scenario_test_env.items():
            client = env["client"]
            independent_dramaworld_for_scenario = env["drama_instance"]

            print(f"\n  -- 处理场景: {scenario_key} --")
            
            # Temporarily override dependency for this interaction
            app.dependency_overrides[get_dramaworld] = lambda: independent_dramaworld_for_scenario

            try:
                interact_response = client.post("/api/interact", json=user_input)
                
                assert interact_response.status_code == 200, \
                    f"[{scenario_key}] 交互API调用失败 (状态码: {interact_response.status_code}): {interact_response.text}"
                
                response_data = interact_response.json()
                assert "error" not in response_data or response_data.get("error") is None, \
                    f"[{scenario_key}] 交互时返回错误: {response_data.get('error')}"
                
                npc_actions = response_data.get("action", [])
                current_state = response_data.get("state", {})

                if not npc_actions:
                    print(f"  ⚠️ 警告: 场景 '{scenario_key}' 在此轮次中返回了空的 'action' 列表。这可能表示NPC未生成任何行为。")

                # Get export records
                export_records_response = client.post("/api/info", json={"help": "export_records"})
                assert export_records_response.status_code == 200, \
                    f"[{scenario_key}] 获取导出记录失败: {export_records_response.text}"
                exported_records = export_records_response.json().get("allmemory", [])
                exported_chunks = export_records_response.json().get("chunks", [])

                turn_data["scenario_outputs"][scenario_key] = {
                    "npc_actions": npc_actions,
                    "current_state": current_state,
                    "exported_records": exported_records,
                    "exported_chunks": exported_chunks,
                }
                print(f"  ✅ 场景 '{scenario_key}' 处理完毕。")
            
            except AssertionError as e:
                print(f"❌ 场景 '{scenario_key}' 对话轮次 {i+1} 失败: {e}")
                raise 
            except Exception as e:
                print(f"❌ 场景 '{scenario_key}' 对话轮次 {i+1} 发生意外错误: {e}")
                import traceback
                print(traceback.format_exc())
                raise
            finally:
                # Clean up dependency override after each interaction
                app.dependency_overrides = {}

        full_report["dialogue_rounds"].append(turn_data)

    # 3. 将最终的对比报告保存到文件
    print("\n--- [阶段三: 生成最终对比报告] ---")
    output_filename = f"e2e_drama_report_{full_report['test_run_timestamp']}.json"
    final_output_path = os.path.join(REPORTS_DIR, output_filename)
    
    with open(final_output_path, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, ensure_ascii=False, indent=4)

    print(f"\n🎉🎉🎉 对比测试完成！详细报告已保存至: {final_output_path} 🎉🎉🎉")
    print("="*80)


@pytest.mark.asyncio
async def test_transform_initial_state():
    """
    测试 `POST /api/data` 接口更新剧本初始状态中除 `mode` 以外的其他变量的功能。
    这个测试将使用独立的 DRAMA 实例。
    """
    print("\n\n--- [测试: 更新初始状态其他变量 (通过 /api/data)] ---")
    
    # Create a new, independent DRAMA instance for this test
    independent_dramaworld_for_test_update = DRAMA()
    
    # Override the dependency for this specific test client
    app.dependency_overrides[get_dramaworld] = lambda: independent_dramaworld_for_test_update
    
    client = TestClient(app)

    try:
        # 1. Load an initial script (e.g., Harry Potter)
        initial_script_name = "load-script-hp"
        load_response = client.post("/api/load", json={"script_name": initial_script_name, "storageMode": True})
        assert load_response.status_code == 200, f"加载剧本失败: {load_response.text}"
        print(f"    ✅ 初始剧本 '{initial_script_name}' 加载成功。")

        # Get current state
        initial_state_response = client.get("/api/data")
        assert initial_state_response.status_code == 200, f"获取初始状态失败: {initial_state_response.text}"
        initial_state_data = initial_state_response.json()
        
        # Use transform_from_state_response helper function
        initial_state_payload = transform_from_state_response(initial_state_data)
        
        # 2. Modify some variables: player_name, background_narrative, a character's profile, and add a new character
        updated_player_name = "Hermione" # Change player to Hermione
        updated_narrative = "A brand new magical adventure begins with a twist!"
        
        # Modify existing character profile (assuming 'Harry' exists in 'load-script-hp')
        existing_char_id = "Harry" 
        found_existing_char = False
        for char_data in initial_state_payload["characters"]:
            if char_data["id"] == existing_char_id:
                char_data["profile"] = "A highly intelligent and resourceful wizard, now with enhanced spellcasting abilities."
                found_existing_char = True
                break
        if not found_existing_char: 
            print(f"    ⚠️ 警告: 剧本 '{initial_script_name}' 中未找到角色 '{existing_char_id}'。请检查剧本以确保测试有效。")

        # Add a new character
        new_character_id = "Dobby The Elf"
        new_character_profile = "A loyal house-elf seeking to help his new friends."
        new_character_initial_memory = "Dobby is free! Dobby is a free elf!"
        
        initial_state_payload["characters"].append(CharacterRequest(
            id=new_character_id, 
            profile=new_character_profile, 
            initial_memory=new_character_initial_memory
        ).model_dump(exclude_unset=True))

        # Update top-level variables
        initial_state_payload["player_name"] = updated_player_name
        initial_state_payload["background_narrative"] = updated_narrative
        
        # 3. Send update request to /api/data
        print(f"    ➡️ 正在通过 /api/data 更新剧本数据...")
        update_response = client.post("/api/data", json=initial_state_payload)
        
        assert update_response.status_code == 200, f"更新初始状态失败 (状态码: {update_response.status_code}): {update_response.text}"
        print(f"    ✅ 初始状态更新请求成功。")

        # 4. Verify updates
        current_state_after_update_response = client.get("/api/data")
        assert current_state_after_update_response.status_code == 200, f"获取更新后状态失败: {current_state_after_update_response.text}"
        current_state_after_update = current_state_after_update_response.json()
        
        assert current_state_after_update.get("player_name") == updated_player_name, \
            f"玩家名称更新失败。预期: {updated_player_name}, 实际: {current_state_after_update.get('player_name')}"
        
        assert current_state_after_update.get("background_narrative") == updated_narrative, \
            f"背景叙述更新失败。预期: {updated_narrative}, 实际: {current_state_after_update.get('background_narrative')}"

        # Check if existing character profile is updated
        if found_existing_char: 
            assert existing_char_id in current_state_after_update["characters"], \
                f"更新后的状态中未找到预期的现有角色 {existing_char_id}。"
            assert current_state_after_update["characters"][existing_char_id]["profile"] == "A highly intelligent and resourceful wizard, now with enhanced spellcasting abilities.", \
                f"现有角色 {existing_char_id} 的 profile 更新失败。"

        # Check if new character is added
        assert new_character_id in current_state_after_update["characters"], \
            f"新角色 {new_character_id} 未被添加。"
        assert current_state_after_update["characters"][new_character_id]["profile"] == new_character_profile, \
            f"新角色 {new_character_id} 的 profile 不匹配。"
        
        # Check if new character's initial memory is correctly set (via the independent dramaworld instance)
        assert new_character_id in independent_dramaworld_for_test_update.dramallm.script["background"]["context"], \
            f"新角色 {new_character_id} 的初始记忆未在 script context 中找到。"
        assert independent_dramaworld_for_test_update.dramallm.script["background"]["context"][new_character_id] == new_character_initial_memory, \
            f"新角色 {new_character_id} 的初始记忆不匹配。"

        print("    🎉 玩家名称、背景叙述、角色profile及新增角色测试通过！")
        print("="*80 + "\n")

    except AssertionError as e:
        print(f"❌ 更新初始状态其他变量测试失败: {e}")
        raise 
    except Exception as e:
        print(f"❌ 更新初始状态其他变量测试中发生意外错误: {e}")
        import traceback
        print(traceback.format_exc())
        raise
    finally:
        # Clean up dependency override after the test
        app.dependency_overrides = {}