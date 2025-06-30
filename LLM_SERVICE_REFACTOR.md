# LLM服务架构重构总结

## 重构目标

将原本丑陋的query_fct参数传递方式重构为优雅的全局LLM服务架构，支持多种模型提供商。

## 架构变化

### 重构前 (旧架构)
```python
# 每个类都需要传递query_fct参数
char = CharacterLLM(query_fct=query)
drama = DramaLLM(query_fct=query)

# 在类内部使用
response = self.query_fct(prompt)
```

### 重构后 (新架构)
```python
# main.py中初始化全局服务
from models import init_llm_service
llm_service = init_llm_service()

# 类不再需要query_fct参数
char = CharacterLLM()
drama = DramaLLM()

# 在类内部使用全局服务
from models import get_llm_service
response = get_llm_service().query(prompt)
```

## 新增文件

### 1. `models.py` - 核心模型管理系统
- `BaseLLMProvider`: 抽象基类
- `AzureOpenAIProvider`: Azure OpenAI实现
- `DeepSeekProvider`: DeepSeek实现  
- `OpenAIProvider`: OpenAI实现
- `LLMManager`: 统一管理器
- `LLMService`: 全局服务类

### 2. 测试文件
- `test_models.py`: 模型功能测试
- `test_llm_service.py`: 架构重构测试

### 3. 文档
- `models_README.md`: 使用说明
- `LLM_SERVICE_REFACTOR.md`: 重构总结

## 修改的文件

### 1. `.env` - 环境配置
```env
# 新增LLM提供商选择
LLM_PROVIDER=azure_openai

# 重新组织配置项
AZURE_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
OPENAI_API_KEY=your_key
```

### 2. `main.py` - 全局服务初始化
```python
# 新增导入
from models import init_llm_service, get_llm_service

# 初始化全局LLM服务
llm_service = init_llm_service()

# 新增prompt_global_character支持
class Prompt(BaseModel):
    # ... 其他字段
    prompt_global_character: str
```

### 3. `frame.py` - 移除query_fct依赖
```python
# 新增导入
from models import get_llm_service

# CharacterLLM类
class CharacterLLM(Character):
    def __init__(self, id=None, config={}, storage_mode=False, retrieve_threshold=1):
        # 移除query_fct参数
        super().__init__(id, config)
        # 移除self.query_fct = query_fct

# DramaLLM类  
class DramaLLM(World):
    def __init__(self, script, storage_mode=True, storager=MemoryStorage(), retrieve_threshold=1):
        # 移除query_fct参数
        super().__init__(script, storage_mode, storager)
        # 移除self.query_fct = query_fct

# 所有方法中的调用
# 旧: response = self.query_fct(prompt)
# 新: response = get_llm_service().query(prompt)
```

### 4. `utils.py` - 简化导入
```python
# 移除旧的query_gpt4实现
# 新增导入
from models import query, aquery
```

### 5. 前端文件
- `index.html`: 新增prompt_global_character输入框
- `components/promptManager.js`: 新增字段支持

## 支持的模型提供商

### 1. Azure OpenAI (默认)
```env
LLM_PROVIDER=azure_openai
AZURE_API_KEY=your_key
AZURE_ENDPOINT=your_endpoint
AZURE_DEPLOYMENT=gpt-4o
```

### 2. DeepSeek
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key
DEEPSEEK_API_URL=https://api.deepseek.com
DEEPSEEK_MODEL=DeepSeek-V3
```

### 3. OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

## 使用方式

### 1. 兼容性调用（推荐）
```python
from utils import query_gpt4  # 自动使用新架构
response = query_gpt4("你好")
```

### 2. 直接使用服务
```python
from models import get_llm_service
service = get_llm_service()
response = service.query("你好")
```

### 3. 异步调用
```python
from models import aquery_gpt4
response = await aquery_gpt4("你好")
```

### 4. 切换提供商
```python
from models import get_llm_service
service = get_llm_service()
service.switch_provider("deepseek")
```

## 优势

### 1. 代码优雅性
- ❌ 旧: 每个类都需要传递query_fct参数
- ✅ 新: 全局服务，无需参数传递

### 2. 可维护性
- ❌ 旧: 修改LLM调用需要改多个地方
- ✅ 新: 统一管理，修改一处即可

### 3. 可扩展性
- ❌ 旧: 添加新模型需要修改多个文件
- ✅ 新: 只需添加新的Provider类

### 4. 配置灵活性
- ❌ 旧: 硬编码API配置
- ✅ 新: 环境变量配置，支持多提供商

### 5. 异步支持
- ❌ 旧: 只支持同步调用
- ✅ 新: 原生支持异步调用

### 6. 向后兼容
- ✅ 现有代码无需修改
- ✅ 保持原有API接口

## 测试验证

运行测试脚本验证重构效果：

```bash
# 测试模型功能
python test_models.py

# 测试架构重构
python test_llm_service.py
```

## 迁移指南

### 对于现有代码
无需修改，自动使用新架构：
```python
from utils import query_gpt4  # 自动使用新的LLM服务
response = query_gpt4("你好")
```

### 对于新代码
推荐使用新的API：
```python
from models import get_llm_service, aquery_gpt4

# 同步调用
service = get_llm_service()
response = service.query("你好")

# 异步调用
response = await aquery_gpt4("你好")
```

## 总结

这次重构成功地将丑陋的参数传递方式改为优雅的全局服务架构，同时：

1. ✅ 保持了向后兼容性
2. ✅ 支持多种模型提供商
3. ✅ 提供了异步调用能力
4. ✅ 简化了代码结构
5. ✅ 提高了可维护性和可扩展性

代码现在更加优雅、易于维护，并且为未来的扩展奠定了良好的基础。
