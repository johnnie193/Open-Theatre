import pytest
from fastapi.testclient import TestClient
import json
import os
import datetime

# 从您的主应用文件中导入 app 对象
# 假设您的 FastAPI 应用实例名为 app，且文件为 main.py
from main import app

# 确保用于存储记录的目录存在
os.makedirs("test_records", exist_ok=True)

# 模拟的多轮对话输入 (使用您提供的新版英文对话)
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

def test_drama_e2e_flow():
    """
    端到端的测试函数，以对话为中心，对比v1/v2模式及不同storage_mode下的响应。
    """
    scenarios = [
        {"script_name": "load-script-station", "mode": "v2", "storage_mode": True},
        {"script_name": "load-script-station", "mode": "v2", "storage_mode": False},
        {"script_name": "load-script-station", "mode": "v1", "storage_mode": True},
        {"script_name": "load-script-station", "mode": "v1", "storage_mode": False},
    ]

    scenario_clients = {}

    # 1. 初始化所有场景的客户端并加载剧本
    print("\n----- [阶段一: 初始化所有测试场景] -----")
    for scenario in scenarios:
        scenario_key = f"mode_{scenario['mode']}_storage_{scenario['storage_mode']}"
        print(f"  正在设置场景: {scenario_key}...")
        
        client = TestClient(app)
        
        # 加载剧本，设置正确的 storage_mode
        load_response = client.post("/api/load", json={"script_name": scenario["script_name"], "storageMode": scenario["storage_mode"]})
        assert load_response.status_code == 200, f"[{scenario_key}] 加载剧本失败: {load_response.text}"
        
        # 获取当前状态，用于后续可能的模式更新
        initial_state_response = client.get("/api/data")
        assert initial_state_response.status_code == 200, f"[{scenario_key}] 获取初始状态失败: {initial_state_response.text}"
        initial_state = initial_state_response.json()
        
        current_scene_id = "scene" + str(initial_state.get("scene_cnt", 1))

        # 如果当前模式与目标模式不符，则更新它
        if initial_state["scenes"][current_scene_id]["mode"] != scenario["mode"]:
            print(f"    -> 模式不匹配，正在更新为 '{scenario['mode']}'...")
            
            # 更新状态字典中的模式
            initial_state["scenes"][current_scene_id]["mode"] = scenario["mode"]
            
            # 将完整的状态（state）转换为符合 ScriptData 模型的 payload
            # 这是为了调用 POST /api/data 接口来重新加载和初始化 dramaworld
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
            
            update_response = client.post("/api/data", json=transform_initial_state)
            print(f"Response Status Code: {update_response.status_code}")
            print(f"Response Headers: {update_response.headers}")
            try:
                print(f"Response JSON: {update_response.json()}")
            except Exception as e:
                print(f"Could not parse response as JSON: {e}")
                print(f"Response Text: {update_response.text}") # Fallback to raw text
            assert update_response.status_code == 200, f"[{scenario_key}] 更新模式失败: {update_response.text}"
        
        scenario_clients[scenario_key] = client
        print(f"  场景 '{scenario_key}' 设置完毕。")

    # 2. 按顺序执行每一轮对话，并收集所有场景的响应
    print("\n----- [阶段二: 逐轮执行对话并对比响应] -----")
    dialogue_comparison_report = []

    for i, user_input in enumerate(DIALOGUE_INPUTS):
        print(f"\n[对话轮次 {i+1}]:")
        print(f"  玩家输入: {user_input}")

        turn_report = {
            "user_input": user_input,
            "responses": {}
        }

        for scenario_key, client in scenario_clients.items():
            interact_response = client.post("/api/interact", json=user_input)
            assert interact_response.status_code == 200, f"[{scenario_key}] 交互API调用失败: {interact_response.text}"
            
            response_data = interact_response.json()
            assert "error" not in response_data, f"[{scenario_key}] 交互时返回错误: {response_data.get('error')}"
            
            # 我们只关心NPC的响应动作 `action`
            turn_report["responses"][scenario_key] = response_data.get("action", [])
            print(f"  -> 来自 '{scenario_key}' 的NPC响应: {response_data.get('action', [])}")

        dialogue_comparison_report.append(turn_report)

    # 3. 将最终的对比报告保存到文件
    print("\n----- [阶段三: 生成最终对比报告] -----")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    final_output_path = f"test_records/comparison_report_{timestamp}.json"
    
    final_report = {
        "test_run_timestamp": timestamp,
        "dialogue_comparison": dialogue_comparison_report
    }

    with open(final_output_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, ensure_ascii=False, indent=4)

    print(f"\n🎉🎉🎉 对比测试完成！报告已保存至: {final_output_path} 🎉🎉")

if __name__ == "__main__":
    # 您可以直接运行此脚本，但推荐使用 `pytest` 命令
    # 例如： pytest -s -v test_main.py
    pytest.main(['-s', '-v', __file__])
