#!/usr/bin/env python3
"""
测试新的模型管理系统
"""

import asyncio
from models import LLMManager, query_gpt4, aquery_gpt4

def test_sync_query():
    """测试同步查询"""
    print("=== 测试同步查询 ===")
    
    # 测试简单查询
    response = query_gpt4("你好，请简单介绍一下你自己。")
    print(f"简单查询响应: {response[:100]}...")
    
    # 测试带系统消息的查询
    response = query_gpt4("请用一句话总结人工智能的发展。", sys="你是一个AI专家。")
    print(f"带系统消息的查询响应: {response[:100]}...")

async def test_async_query():
    """测试异步查询"""
    print("\n=== 测试异步查询 ===")
    
    # 测试异步查询
    response = await aquery_gpt4("请用一句话描述机器学习。")
    print(f"异步查询响应: {response[:100]}...")

def test_different_providers():
    """测试不同的提供商"""
    print("\n=== 测试不同提供商 ===")
    
    providers = ['azure_openai', 'deepseek']
    
    for provider in providers:
        try:
            print(f"\n测试提供商: {provider}")
            manager = LLMManager(provider)
            response = manager.query("请说'你好'")
            print(f"{provider} 响应: {response[:50]}...")
        except Exception as e:
            print(f"{provider} 测试失败: {e}")

async def test_concurrent_requests():
    """测试并发请求"""
    print("\n=== 测试并发请求 ===")
    
    tasks = []
    for i in range(3):
        task = aquery_gpt4(f"请回答问题{i+1}: 1+{i+1}等于多少？")
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks)
    for i, response in enumerate(responses):
        print(f"并发请求{i+1}响应: {response[:50]}...")

def main():
    """主测试函数"""
    print("开始测试新的模型管理系统...")
    
    try:
        # 测试同步功能
        test_sync_query()
        
        # 测试不同提供商
        test_different_providers()
        
        # 测试异步功能
        print("\n开始异步测试...")
        asyncio.run(test_async_query())
        asyncio.run(test_concurrent_requests())
        
        print("\n✅ 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
