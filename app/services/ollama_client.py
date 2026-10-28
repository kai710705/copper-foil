"""Ollama Vision API 用戶端；不把認證或外部錯誤暴露給使用者。"""
import base64
import json
from urllib import error as url_error
from urllib import request


class OllamaClientError(Exception):
    """可安全顯示給應用程式的 Ollama 錯誤。"""


class OllamaConfigurationError(OllamaClientError):
    pass


class OllamaProviderError(OllamaClientError):
    pass


class OllamaClient:
    def __init__(self, base_url, api_key, model, timeout=30, max_image_bytes=4 * 1024 * 1024,
                 opener=request.urlopen):
        self.base_url = (base_url or '').rstrip('/')
        self.api_key = api_key or ''
        self.model = model
        self.timeout = timeout
        self.max_image_bytes = max_image_bytes
        self.opener = opener

    def analyze(self, image_bytes, prompt):
        if not self.base_url or not self.api_key:
            raise OllamaConfigurationError('影像辨識服務尚未完成設定')
        if not image_bytes:
            raise OllamaProviderError('沒有可供辨識的影像')
        if len(image_bytes) > self.max_image_bytes:
            raise OllamaProviderError('影像大小超過辨識限制')
        payload = {
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt,
                          'images': [base64.b64encode(image_bytes).decode('ascii')]}],
            'format': 'json',
            'stream': False,
        }
        body = json.dumps(payload).encode('utf-8')
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.api_key}'}
        req = request.Request(f'{self.base_url}/api/chat', data=body, headers=headers, method='POST')
        try:
            with self.opener(req, timeout=self.timeout) as response:
                raw = response.read()
        except (url_error.URLError, TimeoutError, OSError) as exc:
            raise OllamaProviderError('影像辨識服務暫時無法連線') from exc
        try:
            result = json.loads(raw.decode('utf-8'))
            content = result['message']['content']
        except (ValueError, KeyError, TypeError) as exc:
            raise OllamaProviderError('影像辨識服務回應格式無效') from exc
        if not isinstance(content, str) or not content.strip():
            raise OllamaProviderError('影像辨識服務沒有回傳有效結果')
        return content
