import openai
import google.generativeai as genai
import requests
import time
from abc import ABC, abstractmethod
from config import Config


class BaseModelAdapter(ABC):
    """Base adapter class for calling LLMs."""
    def __init__(self):
        self.max_retries = Config.MAX_RETRIES
        self.timeout = Config.TIMEOUT
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    def _retry_request(self, func, *args, **kwargs):
        """Retry helper with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # exponential backoff


class DoubaoAdapter(BaseModelAdapter):    #can use other LLM models
    def __init__(self, api_key=None):
        super().__init__()
        self.api_key = api_key or Config.DOUBAO_API_KEY
        if not self.api_key:
            raise ValueError("Doubao API key not configured")
        # ByteDance Doubao API endpoint
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"

    def generate_text(self, prompt: str, **kwargs) -> str:
        def _make_request():
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": kwargs.get("model", "ep-20231002173654-zx7kr"),  # Doubao model ID
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": kwargs.get("max_tokens", 1000),
                "temperature": kwargs.get("temperature", 0.7)
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        
        return self._retry_request(_make_request)


class ChatGPTAdapter(BaseModelAdapter):
    def __init__(self, api_key=None):
        super().__init__()
        self.api_key = api_key or Config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        openai.api_key = self.api_key

    def generate_text(self, prompt: str, **kwargs) -> str:
        def _make_request():
            response = openai.chat.completions.create(
                model=kwargs.get("model", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": kwargs.get("system_prompt", "You are a helpful assistant.")},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7),
                timeout=self.timeout
            )
            return response.choices[0].message.content.strip()
        
        return self._retry_request(_make_request)


class GeminiAdapter(BaseModelAdapter):
    def __init__(self, api_key=None):
        super().__init__()
        self.api_key = api_key or Config.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_text(self, prompt: str, **kwargs) -> str:
        def _make_request():
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=kwargs.get("max_tokens", 1000),
                    temperature=kwargs.get("temperature", 0.7),
                )
            )
            return response.text.strip()
        
        return self._retry_request(_make_request)