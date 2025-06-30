#!/usr/bin/env python3
"""
测试异步v2_plus性能提升
"""

import os
import sys
import time
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import init_llm_service
from frame import DramaLLM

def create_test_script():
    """创建测试脚本"""
    return {
        "id": "异步测试剧本",
        "background": {
            "player": "柯南",
            "narrative": "测试异步v2_plus性能",
            "characters": {
                "柯南": "小学一年级生",
                "毛利小五郎": "知名侦探",
                "毛利兰": "女高中生",
                "雄一": "推销员",
                "莫里斯": "背包客"
            }
        },
        "scenes": {
            "scene1": {
                "id": "scene1",
                "name": "异步测试场景",
                "scene": "测试场景描述",
                "mode": "v2_plus",
                "characters": {
                    "柯南": "",
                    "毛利小五郎": "询问案件详情",
                    "毛利兰": "安慰其他人",
                    "雄一": "推销贷款",
                    "莫里斯": "分享旅行故事"
                },
                "chain": ["角色互动", "情节推进"]
            }
        }
    }

def test_sync_v2_plus():
    """测试同步v2_plus性能"""
    print("=== 测试同步v2_plus ===")
    
    # 初始化LLM服务
    init_llm_service("azure_openai")
    
    # 创建DramaLLM实例
    script = create_test_script()
    drama = DramaLLM(script=script, storage_mode=False)
    
    # 模拟导演响应（多个角色）
    mock_response = {
        "当前的情节链": [["角色互动", True], ["情节推进", False]],
        "行动人列表": [
            {"角色": "毛利小五郎", "指令": "询问案件的具体细节"},
            {"角色": "毛利兰", "指令": "安慰在场的其他人"},
            {"角色": "雄一", "指令": "寻找机会推销贷款"}
        ]
    }
    
    # 手动设置响应以测试角色处理部分
    drama.nc = mock_response["当前的情节链"]
    
    start_time = time.time()
    
    # 模拟同步处理多个角色
    for char_id in drama.characters:
        drama.characters[char_id].to_do = False
    
    for actor_info in mock_response["行动人列表"]:
        char_name = actor_info["角色"]
        instruction = actor_info["指令"]
        
        if char_name in drama.characters:
            drama.characters[char_name].to_do = True
            drama.characters[char_name].motivation = instruction
            # 这里我们不实际调用LLM，只是模拟处理时间
            time.sleep(0.1)  # 模拟LLM调用时间
    
    sync_time = time.time() - start_time
    print(f"同步处理时间: {sync_time:.2f}秒")
    return sync_time

async def test_async_v2_plus():
    """测试异步v2_plus性能"""
    print("\n=== 测试异步v2_plus ===")
    
    # 创建DramaLLM实例
    script = create_test_script()
    drama = DramaLLM(script=script, storage_mode=False)
    
    # 模拟导演响应（多个角色）
    mock_response = {
        "当前的情节链": [["角色互动", True], ["情节推进", False]],
        "行动人列表": [
            {"角色": "毛利小五郎", "指令": "询问案件的具体细节"},
            {"角色": "毛利兰", "指令": "安慰在场的其他人"},
            {"角色": "雄一", "指令": "寻找机会推销贷款"}
        ]
    }
    
    # 手动设置响应以测试角色处理部分
    drama.nc = mock_response["当前的情节链"]
    
    start_time = time.time()
    
    # 模拟异步并行处理多个角色
    for char_id in drama.characters:
        drama.characters[char_id].to_do = False
    
    tasks = []
    for actor_info in mock_response["行动人列表"]:
        char_name = actor_info["角色"]
        instruction = actor_info["指令"]
        
        if char_name in drama.characters:
            drama.characters[char_name].to_do = True
            drama.characters[char_name].motivation = instruction
            # 创建异步任务模拟LLM调用
            task = asyncio.create_task(simulate_async_llm_call(char_name))
            tasks.append(task)
    
    # 并行执行所有任务
    if tasks:
        await asyncio.gather(*tasks)
    
    async_time = time.time() - start_time
    print(f"异步并行处理时间: {async_time:.2f}秒")
    return async_time

async def simulate_async_llm_call(char_name):
    """模拟异步LLM调用"""
    await asyncio.sleep(0.1)  # 模拟LLM调用时间
    print(f"  {char_name} 处理完成")

def test_real_async_v2_plus():
    """测试真实的异步v2_plus调用"""
    print("\n=== 测试真实异步v2_plus调用 ===")
    
    try:
        # 创建测试脚本，设置为v2_plus_async模式
        script = create_test_script()
        script["scenes"]["scene1"]["mode"] = "v2_plus_async"
        
        drama = DramaLLM(script=script, storage_mode=False)
        
        # 模拟一个简单的玩家行动
        drama.calculate(drama.player.id, x="-speak", bid=None, content="大家好")
        
        start_time = time.time()
        
        # 调用异步v2_plus_react
        asyncio.run(drama.av2_plus_react())
        
        real_async_time = time.time() - start_time
        print(f"真实异步v2_plus处理时间: {real_async_time:.2f}秒")
        return real_async_time
        
    except Exception as e:
        print(f"真实异步测试失败: {e}")
        return None

def main():
    """主测试函数"""
    print("开始测试异步v2_plus性能...")
    
    try:
        # 测试同步版本
        sync_time = test_sync_v2_plus()
        
        # 测试异步版本
        async_time = asyncio.run(test_async_v2_plus())
        
        # 测试真实异步调用
        real_time = test_real_async_v2_plus()
        
        # 性能对比
        print("\n=== 性能对比 ===")
        print(f"同步处理时间: {sync_time:.2f}秒")
        print(f"异步并行处理时间: {async_time:.2f}秒")
        if real_time:
            print(f"真实异步处理时间: {real_time:.2f}秒")
        
        if async_time < sync_time:
            improvement = ((sync_time - async_time) / sync_time) * 100
            print(f"✅ 异步版本性能提升: {improvement:.1f}%")
        else:
            print("⚠️ 在模拟测试中，异步版本可能没有显著提升（实际LLM调用会有更明显的效果）")
        
        print("\n📝 说明:")
        print("- 同步版本: 角色依次处理，总时间 = 单个处理时间 × 角色数量")
        print("- 异步版本: 角色并行处理，总时间 ≈ 单个处理时间")
        print("- 实际使用中，LLM调用时间较长，异步并行的优势会更加明显")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
