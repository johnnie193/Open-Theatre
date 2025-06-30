# LLM Models Management System

一个优雅的多模型提供商管理系统，支持同步和异步调用。

## 支持的提供商

- **Azure OpenAI** (`azure_openai`) - 默认提供商
- **DeepSeek** (`deepseek`) - 支持DeepSeek V3模型
- **OpenAI** (`openai`) - 标准OpenAI API

## 配置

在 `.env` 文件中配置：

```env
# LLM提供商选择 (azure_openai, deepseek, openai)
LLM_PROVIDER=azure_openai

# Azure OpenAI 配置
AZURE_DEPLOYMENT=gpt-4o
AZURE_API_VERSION=2024-08-01-preview
AZURE_ENDPOINT=https://euinstance.openai.azure.com/
AZURE_API_KEY=your_azure_api_key

# DeepSeek 配置
DEEPSEEK_API_URL=https://api.deepseek.com
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=DeepSeek-V3

# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

## 使用方法

### 1. 兼容性接口（推荐）

```python
from models import query_gpt4, aquery_gpt4

# 同步调用
response = query_gpt4("你好，请介绍一下你自己。")

# 带系统消息
response = query_gpt4("请总结AI发展", sys="你是一个AI专家")

# 异步调用
import asyncio
response = await aquery_gpt4("请用一句话描述机器学习")
```

### 2. 直接使用管理器

```python
from models import LLMManager

# 使用默认提供商
manager = LLMManager()
response = manager.query("你好")

# 指定提供商
manager = LLMManager("deepseek")
response = manager.query("你好")

# 异步调用
response = await manager.aquery("你好")
```

### 3. 高级用法

```python
from models import LLMManager

manager = LLMManager()

# 自定义参数
response = manager.query(
    "请写一首诗",
    temperature=0.8,
    max_tokens=500
)

# 使用消息列表格式
messages = [
    {"role": "system", "content": "你是一个诗人"},
    {"role": "user", "content": "请写一首关于春天的诗"}
]
response = manager.query(messages)
```

### 4. 并发请求

```python
import asyncio
from models import aquery_gpt4

async def concurrent_requests():
    tasks = [
        aquery_gpt4("问题1"),
        aquery_gpt4("问题2"),
        aquery_gpt4("问题3")
    ]
    responses = await asyncio.gather(*tasks)
    return responses

# 运行并发请求
responses = asyncio.run(concurrent_requests())
```

## 切换提供商

### 方法1: 环境变量（全局）

在 `.env` 文件中修改：
```env
LLM_PROVIDER=deepseek
```

### 方法2: 代码中指定（局部）

```python
from models import LLMManager

# 使用Azure OpenAI
azure_manager = LLMManager("azure_openai")
response1 = azure_manager.query("你好")

# 使用DeepSeek
deepseek_manager = LLLManager("deepseek")
response2 = deepseek_manager.query("你好")
```

## 错误处理

```python
from models import LLMManager

manager = LLMManager()

try:
    response = manager.query("你好")
    print(response)
except Exception as e:
    print(f"API调用失败: {e}")
```

## 测试

运行测试脚本：

```bash
python test_models.py
```

## 迁移指南

### 从旧版本迁移

旧代码：
```python
from utils import query_gpt4

response = query_gpt4("你好")
```

新代码（无需修改）：
```python
from utils import query_gpt4  # 自动使用新的模型系统

response = query_gpt4("你好")
```

### 使用新功能

```python
from models import aquery_gpt4, LLMManager

# 异步调用
response = await aquery_gpt4("你好")

# 切换模型
manager = LLMManager("deepseek")
response = manager.query("你好")
```

## 架构说明

- `BaseLLMProvider`: 抽象基类，定义统一接口
- `AzureOpenAIProvider`: Azure OpenAI实现
- `DeepSeekProvider`: DeepSeek实现  
- `OpenAIProvider`: OpenAI实现
- `LLMManager`: 统一管理器，负责提供商选择和调用
- 兼容性函数: `query_gpt4`, `aquery_gpt4` 保持向后兼容

## 优势

1. **统一接口**: 所有提供商使用相同的调用方式
2. **易于切换**: 通过配置文件或代码轻松切换提供商
3. **异步支持**: 原生支持异步调用，提高性能
4. **向后兼容**: 现有代码无需修改
5. **错误处理**: 统一的错误处理和日志记录
6. **可扩展**: 易于添加新的模型提供商
