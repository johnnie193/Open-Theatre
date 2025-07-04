"""
LLM Models Management System
支持多种模型提供商的统一接口
"""

import os
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class BaseLLMProvider(ABC):
    """LLM提供商基类"""
    
    def __init__(self, **kwargs):
        self.config = kwargs
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """同步聊天完成"""
        pass
    
    @abstractmethod
    async def achat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """异步聊天完成"""
        pass

class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI 提供商"""
    
    def __init__(self):
        super().__init__()
        from openai import AzureOpenAI
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_API_KEY"),
            api_version=os.getenv("AZURE_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_ENDPOINT")
        )
        self.model = os.getenv("AZURE_DEPLOYMENT", "gpt-4o")
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """同步聊天完成"""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2000),
                **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Azure OpenAI API调用失败: {e}")
            raise
    
    async def achat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """异步聊天完成"""
        try:
            from openai import AsyncAzureOpenAI
            async_client = AsyncAzureOpenAI(
                api_key=os.getenv("AZURE_API_KEY"),
                api_version=os.getenv("AZURE_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_ENDPOINT")
            )
            completion = await async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2000),
                **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Azure OpenAI Async API调用失败: {e}")
            raise

class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek 提供商"""
    
    def __init__(self):
        super().__init__()
        self.api_url = os.getenv("DEEPSEEK_API_URL")
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.model = os.getenv("DEEPSEEK_MODEL", "DeepSeek-V3")
        
        import httpx
        self.sync_client = httpx.Client(timeout=30.0)
        self.async_client = httpx.AsyncClient(timeout=30.0)
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """同步聊天完成"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            payload = {
                'model': self.model,
                'messages': messages,
                'temperature': kwargs.get('temperature', 0.3),
                'max_tokens': kwargs.get('max_tokens', 2000),
                'top_p': kwargs.get('top_p', 0.9)
            }
            
            response = self.sync_client.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"DeepSeek API调用失败: {response.status_code}, {response.text}")
                raise Exception(f"API调用失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            raise
    
    async def achat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """异步聊天完成"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            payload = {
                'model': self.model,
                'messages': messages,
                'temperature': kwargs.get('temperature', 0.3),
                'max_tokens': kwargs.get('max_tokens', 2000),
                'top_p': kwargs.get('top_p', 0.9)
            }
            
            response = await self.async_client.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"DeepSeek Async API调用失败: {response.status_code}, {response.text}")
                raise Exception(f"API调用失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"DeepSeek Async API调用失败: {e}")
            raise

class OpenAIProvider(BaseLLMProvider):
    """OpenAI 提供商"""
    
    def __init__(self):
        super().__init__()
        from openai import OpenAI
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """同步聊天完成"""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2000),
                **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise
    
    async def achat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """异步聊天完成"""
        try:
            from openai import AsyncOpenAI
            async_client = AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL")
            )
            completion = await async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2000),
                **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI Async API调用失败: {e}")
            raise

# 模型提供商注册表
PROVIDERS = {
    'azure_openai': AzureOpenAIProvider,
    'deepseek': DeepSeekProvider,
    'openai': OpenAIProvider,
}

class LLMManager:
    """LLM管理器"""
    
    def __init__(self, provider_name: str = None):
        self.provider_name = provider_name or os.getenv("LLM_PROVIDER", "azure_openai")
        self.provider = self._get_provider()
    
    def _get_provider(self) -> BaseLLMProvider:
        """获取提供商实例"""
        if self.provider_name not in PROVIDERS:
            raise ValueError(f"不支持的提供商: {self.provider_name}. 支持的提供商: {list(PROVIDERS.keys())}")
        
        return PROVIDERS[self.provider_name]()
    
    def query(self, prompt: Union[str, List[Dict[str, str]]], system: str = None, **kwargs) -> str:
        """统一查询接口（同步）"""
        messages = self._prepare_messages(prompt, system)
        return self.provider.chat_completion(messages, **kwargs)
    
    async def aquery(self, prompt: Union[str, List[Dict[str, str]]], system: str = None, **kwargs) -> str:
        """统一查询接口（异步）"""
        messages = self._prepare_messages(prompt, system)
        return await self.provider.achat_completion(messages, **kwargs)
    
    def _prepare_messages(self, prompt: Union[str, List[Dict[str, str]]], system: str = None) -> List[Dict[str, str]]:
        """准备消息格式"""
        if isinstance(prompt, list):
            return prompt
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return messages

# 全局LLM服务实例
_global_llm_service = None

class LLMService:
    """全局LLM服务类"""

    def __init__(self, provider_name: str = None):
        self.manager = LLMManager(provider_name)

    def query(self, prompt: Union[str, List[Dict[str, str]]], sys: str = None, **kwargs) -> str:
        """同步查询"""
        return self.manager.query(prompt, sys, **kwargs)

    async def aquery(self, prompt: Union[str, List[Dict[str, str]]], sys: str = None, **kwargs) -> str:
        """异步查询"""
        return await self.manager.aquery(prompt, sys, **kwargs)

    def switch_provider(self, provider_name: str):
        """切换提供商"""
        self.manager = LLMManager(provider_name)

def init_llm_service(provider_name: str = None) -> LLMService:
    """初始化全局LLM服务"""
    global _global_llm_service
    _global_llm_service = LLMService(provider_name)
    return _global_llm_service

def get_llm_service() -> LLMService:
    """获取全局LLM服务实例"""
    global _global_llm_service
    if _global_llm_service is None:
        _global_llm_service = LLMService()
    return _global_llm_service

# 兼容性函数
def query(prompt: Union[str, List[Dict[str, str]]], sys: str = None, **kwargs) -> str:
    """兼容旧版本的query_gpt4函数"""
    return get_llm_service().query(prompt, sys, **kwargs)

async def aquery(prompt: Union[str, List[Dict[str, str]]], sys: str = None, **kwargs) -> str:
    """异步版本的query函数"""
    return await get_llm_service().aquery(prompt, sys, **kwargs)
