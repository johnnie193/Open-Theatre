import pytest
import requests
import json
import os
import datetime

# 定义测试将要连接的基础URL
BASE_URL = "http://127.0.0.1:3000" 

# 确保用于存储记录的目录存在
os.makedirs("test_records", exist_ok=True)

# 模拟的多轮对话输入
# 您可以根据需要调整或扩展这些对话
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

def run_dialogue_flow(session, dialogue_inputs):
    """
    一个辅助函数，用于运行完整的对话流程并收集响应。

    Args:
        session: requests.Session 对象.
        dialogue_inputs: 一个包含对话输入的字典列表。

    Returns:
        一个包含所有API响应的列表。
    """
    responses = []
    for user_input in dialogue_inputs:
        print(f"  [用户输入]: {user_input}")
        response = session.post(f"{BASE_URL}/api/interact", json=user_input)
        assert response.status_code == 200, f"交互API调用失败，状态码: {response.status_code}, 内容: {response.text}"
        
        response_data = response.json()
        assert "error" not in response_data, f"交互时返回错误: {response_data.get('error')}"
        
        print(f"  [应用响应]: {response_data}")
        responses.append(response_data)
        
    return responses

def test_drama_e2e_flow():
    """
    端到端的测试函数，用于测试v1和v2模式下，不同storage_mode的完整流程。
    """
    # 场景可以在这里循环，以便在不同的剧本和设置下运行测试
    scenarios = [
        {"script_name": "load-script-station", "mode": "v2", "storage_mode": True},
        {"script_name": "load-script-station", "mode": "v2", "storage_mode": False},
        {"script_name": "load-script-station", "mode": "v1", "storage_mode": True},
        {"script_name": "load-script-station", "mode": "v1", "storage_mode": False},
    ]

    all_results = {}

    for scenario in scenarios:
        scenario_key = f"{scenario['script_name']}_mode_{scenario['mode']}_storage_{scenario['storage_mode']}"
        print(f"\n----- 开始测试场景: {scenario_key} -----")

        with requests.Session() as session:
            # 1. 加载剧本
            print(f"[步骤 1]: 加载剧本 '{scenario['script_name']}'...")
            load_response = session.post(f"{BASE_URL}/api/load", json={"script_name": scenario["script_name"], "storageMode": scenario["storage_mode"]})
            assert load_response.status_code == 200, f"加载剧本失败，状态码: {load_response.status_code}"
            print("[结果]: 剧本加载成功。")

            # 2. 如果剧本模式与当前场景模式不符，进行更新
            initial_state = load_response.json()
            # print(initial_state)
            current_scene_id = "scene" + str(initial_state.get("scene_cnt", 1))
            
            if initial_state["scenes"][current_scene_id]["mode"] != scenario["mode"]:
                print(f"[步骤 2]: 更新场景模式为 '{scenario['mode']}'...")
                initial_state["scenes"][current_scene_id]["mode"] = scenario["mode"]
                print("initial_state", initial_state)
                
                transform_initial_state = {
                    "id": initial_state["id"],
                    "player_name": initial_state["player_name"],
                    "background_narrative": initial_state["background_narrative"],
                    "characters": [],
                    "scenes": {},
                    "storageMode": scenario["storage_mode"]
                }
                for cid, character in initial_state["characters"].items():
                    transform_initial_state["characters"].append({
                        "id": cid,
                        "profile": character["profile"],
                        "initial_memory": initial_state["script"]["background"]["context"][cid] if initial_state["script"]["background"]["context"] and cid in initial_state["script"]["background"]["context"] else ""
                    })
                for sid, scene in initial_state["scenes"].items():
                    transform_initial_state["scenes"][sid] = {
                        "sceneName": scene["name"],
                        "sceneInfo": scene["info"],
                        "mode": scene["mode"],
                        "characters": list(scene["characters"].keys()),
                        "chains": initial_state["script"]["scenes"][sid]["chain"],
                        "streams": initial_state["script"]["scenes"][sid]["stream"],
                    }
                # print("transform_initial_state", transform_initial_state)
                update_response = session.post(f"{BASE_URL}/api/data", json=transform_initial_state)
                assert update_response.status_code == 200, f"更新数据失败，状态码: {update_response.status_code}"
                print("[结果]: 模式更新成功。")

            # 3. 运行多轮对话
            print("[步骤 3]: 开始模拟多轮对话...")
            dialogue_responses = run_dialogue_flow(session, DIALOGUE_INPUTS)
            print("[结果]: 多轮对话完成。")

            # 4. 导出记录
            print("[步骤 4]: 导出测试记录...")
            info_response = session.post(f"{BASE_URL}/api/info", json={"help": "export_records"})
            assert info_response.status_code == 200, "导出记录请求失败"
            export_data = info_response.json()
            assert "error" not in export_data, f"导出时返回错误: {export_data.get('error')}"
            print("[结果]: 记录导出成功。")

            all_results[scenario_key] = {
                "dialogue_flow": dialogue_responses,
                "exported_records": export_data
            }
        
        print(f"----- 场景测试结束: {scenario_key} -----")

    # 5. 将所有结果保存到一个文件中
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    final_output_path = f"test_records/ultimate_test_report_{timestamp}.json"
    
    print(f"\n[最终步骤]: 将所有测试结果保存到 '{final_output_path}'...")
    with open(final_output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)

    print("\n🎉🎉🎉 终极Pytest测试完成！所有结果已保存。 🎉🎉🎉")

if __name__ == "__main__":
    # 您可以直接运行此脚本，但推荐使用 `pytest` 命令
    # 例如： pytest -s -v test_main.py
    pytest.main(['-s', '-v', __file__])
