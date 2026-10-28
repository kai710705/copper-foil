import json
import sys
import unittest
from pathlib import Path
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.ollama_client import OllamaClient, OllamaConfigurationError, OllamaProviderError


class Response:
    def __init__(self, value):
        self.value = value
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return self.value


class OllamaClientTests(unittest.TestCase):
    def test_sends_base64_image_and_returns_content(self):
        captured = {}
        def opener(req, timeout):
            captured['headers'] = dict(req.headers)
            captured['body'] = json.loads(req.data)
            captured['timeout'] = timeout
            return Response(json.dumps({'message': {'content': '{"helmet":"pass"}'}}).encode())
        result = OllamaClient('https://example.test', 'secret', 'gemma4:31b-cloud', opener=opener).analyze(b'jpg', 'check')
        self.assertEqual(result, '{"helmet":"pass"}')
        self.assertEqual(captured['body']['messages'][0]['images'], ['anBn'])
        self.assertEqual(captured['timeout'], 30)

    def test_missing_configuration_is_rejected(self):
        with self.assertRaises(OllamaConfigurationError):
            OllamaClient('', '', 'gemma4').analyze(b'jpg', 'check')

    def test_provider_timeout_is_normalized(self):
        def opener(*args, **kwargs): raise URLError('secret internal detail')
        with self.assertRaises(OllamaProviderError) as context:
            OllamaClient('https://example.test', 'secret', 'gemma4', opener=opener).analyze(b'jpg', 'check')
        self.assertNotIn('secret internal detail', str(context.exception))


if __name__ == '__main__': unittest.main()
