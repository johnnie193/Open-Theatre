import os
from dotenv import load_dotenv
load_dotenv()

# case 1
# 调用 Azure OpenAI API
from openai import AzureOpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_API_KEY"),
    api_version=os.getenv("AZURE_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT")
)

messages_for_llm = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
]

chat_completion = client.chat.completions.create(
    model=os.getenv("AZURE_DEPLOYMENT"),
    messages=messages_for_llm,
    temperature=0.7,
    max_tokens=1500, # 确保有足够空间生成详细评估
)
evaluation_markdown = chat_completion.choices[0].message.content

# case 1.1
# 调用 OpenAI API
from openai import OpenAI
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)
response = client.chat.completions.create(
    model=os.getenv("OPENAI_MODEL"),
    messages=messages_for_llm,
    temperature=0.7,
    max_tokens=1500, # 确保有足够空间生成详细评估
)
evaluation_markdown = response.choices[0].message.content

# case 2
# 调用 deepseek
import os
import logging
import httpx
logger = logging.getLogger(__name__)
class DeepSeekService:
    """DeepSeek V3 评分服务"""
    
    def __init__(self):
        # DeepSeek V3 配置
        self.DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
        self.DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL")
        
        # 初始化DeepSeek客户端
        import httpx
        self.http_client = httpx.AsyncClient()
    
    async def _call_deepseek_evaluation(self, prompt: str) -> str:
        """调用DeepSeek V3进行评估"""
        try:
            headers = {
                'Authorization': f'Bearer {self.DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json'
            }
            payload = {
                'model': self.DEEPSEEK_MODEL,
                'messages': [
                    {"role": "user", "content": prompt}
                ],
                'temperature': 0.3,  # 较低的温度确保评估的一致性
                'max_tokens': 2000,
                'top_p': 0.9
            }
            response = await self.http_client.post(
                f"{self.DEEPSEEK_API_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"DeepSeek API调用失败: {response.status_code}, {response.text}")
                raise Exception(f"API调用失败: {response.status_code}")
            
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            raise Exception(f"评估服务暂时不可用: {str(e)}")

