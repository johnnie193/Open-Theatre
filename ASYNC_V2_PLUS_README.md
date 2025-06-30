# 异步v2_plus优化说明

## 优化背景

在v2_plus模式中，导演会指定多个角色同时行动，原本的实现是顺序调用每个角色的v2()方法，这导致了不必要的等待时间。通过引入异步并行调用，可以显著提升性能。

## 性能对比

### 原始同步版本
```
角色1 LLM调用 (1秒) → 角色2 LLM调用 (1秒) → 角色3 LLM调用 (1秒)
总时间: 3秒
```

### 优化异步版本
```
角色1 LLM调用 (1秒) ┐
角色2 LLM调用 (1秒) ├─ 并行执行
角色3 LLM调用 (1秒) ┘
总时间: ~1秒
```

## 新增功能

### 1. 异步v2方法 (`av2`)
```python
async def av2(self, narrative, info, scene_id=None, plot=None):
    """异步版本的v2方法"""
    # 使用 await get_llm_service().aquery(prompt) 进行异步调用
```

### 2. 异步v2_plus_react方法 (`av2_plus_react`)
```python
async def av2_plus_react(self):
    """异步版本的v2_plus_react，支持并行处理多个角色"""
    # 1. 异步获取导演指令
    response = await get_llm_service().aquery(director_prompt)
    
    # 2. 为每个角色创建异步任务
    tasks = []
    for actor_info in response["行动人列表"]:
        task = character.av2(...)
        tasks.append(task)
    
    # 3. 并行执行所有角色的LLM调用
    await asyncio.gather(*tasks)
```

### 3. 新的模式支持 (`v2_plus_async`)
在脚本中设置：
```yaml
scenes:
  scene1:
    mode: v2_plus_async  # 使用异步并行版本
```

## 使用方法

### 1. 脚本配置
```yaml
scenes:
  scene1:
    id: scene1
    name: 测试场景
    mode: v2_plus_async  # 关键：使用异步模式
    characters:
      角色1: 指令1
      角色2: 指令2
      角色3: 指令3
```

### 2. API调用
异步模式会自动在main.py中处理：
```python
elif self.dramallm.mode == "v2_plus_async":
    # 异步版本的v2_plus，使用并行处理
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.dramallm.av2_plus_react())
    except RuntimeError:
        asyncio.run(self.dramallm.av2_plus_react())
```

### 3. 性能测试
运行测试脚本：
```bash
python test_async_v2_plus.py
```

## 技术实现

### 1. 异步LLM调用
```python
# 同步版本
response = get_llm_service().query(prompt)

# 异步版本  
response = await get_llm_service().aquery(prompt)
```

### 2. 并行任务执行
```python
# 创建任务列表
tasks = []
for character in active_characters:
    task = character.av2(...)
    tasks.append(task)

# 并行执行
await asyncio.gather(*tasks)
```

### 3. 事件循环处理
```python
# 在同步环境中运行异步代码
try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_function())
except RuntimeError:
    asyncio.run(async_function())
```

## 性能优势

### 1. 时间复杂度
- **同步版本**: O(n) - 线性时间，n为角色数量
- **异步版本**: O(1) - 常数时间（理论上）

### 2. 实际性能提升
假设单个LLM调用需要2秒：

| 角色数量 | 同步时间 | 异步时间 | 性能提升 |
|---------|---------|---------|---------|
| 2个角色  | 4秒     | ~2秒    | 50%     |
| 3个角色  | 6秒     | ~2秒    | 67%     |
| 4个角色  | 8秒     | ~2秒    | 75%     |

### 3. 用户体验改善
- ✅ 响应时间显著减少
- ✅ 多角色场景更加流畅
- ✅ 服务器资源利用率提高

## 兼容性

### 1. 向后兼容
- 原有的`v2_plus`模式继续工作
- 新增`v2_plus_async`模式提供异步支持
- 现有脚本无需修改

### 2. 模式选择
```yaml
# 同步版本（原有）
mode: v2_plus

# 异步版本（新增）
mode: v2_plus_async
```

## 注意事项

### 1. 错误处理
异步版本包含完整的错误处理：
```python
try:
    response = await get_llm_service().aquery(prompt)
except Exception as e:
    # 重试机制
    response = await get_llm_service().aquery(prompt)
```

### 2. 日志记录
异步版本使用独立的日志标识：
```python
self.log(prompt_and_response, 'av2_plus')  # 区别于同步版本的'v2_plus'
```

### 3. 内存使用
并行执行可能会增加内存使用，但通常在可接受范围内。

## 测试验证

### 1. 功能测试
```bash
python test_async_v2_plus.py
```

### 2. 性能基准测试
测试脚本会对比同步和异步版本的性能差异。

### 3. 集成测试
在实际剧本中使用`v2_plus_async`模式验证功能完整性。

## 总结

异步v2_plus优化带来了显著的性能提升：

1. **性能提升**: 多角色场景的响应时间减少50-75%
2. **用户体验**: 更流畅的交互体验
3. **资源利用**: 更好的服务器资源利用率
4. **向后兼容**: 不影响现有功能
5. **易于使用**: 只需修改模式配置即可启用

这个优化特别适合有多个NPC同时行动的复杂剧情场景，能够显著提升整体的交互体验。
