import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.vision_analysis_service import VisionAnalysisService, VisionValidationError


def result_json(**overrides):
    value = {
        'helmet': {'status': 'pass', 'confidence': 0.9, 'evidence': 'ok'},
        'vest': {'status': 'fail', 'confidence': 0.8, 'evidence': 'missing'},
        'barrier': {'status': 'unknown', 'confidence': 0.4, 'evidence': 'not visible'},
        'risk_level': 'warning', 'summary': 'test'
    }
    value.update(overrides)
    return json.dumps(value)


class FakeClient:
    def __init__(self, response): self.response = response
    def analyze(self, image, prompt): return self.response


class VisionAnalysisServiceTests(unittest.TestCase):
    def test_valid_result(self):
        result = VisionAnalysisService(FakeClient(result_json())).analyze_frame(b'jpg')
        self.assertEqual(result.vest.status, 'fail')
        self.assertEqual(result.barrier.status, 'unknown')

    def test_missing_frame_rejected(self):
        with self.assertRaises(VisionValidationError):
            VisionAnalysisService(FakeClient(result_json())).analyze_frame(b'')

    def test_invalid_json_and_confidence_rejected(self):
        with self.assertRaises(VisionValidationError):
            VisionAnalysisService(FakeClient('not-json')).analyze_frame(b'jpg')
        with self.assertRaises(VisionValidationError):
            VisionAnalysisService(FakeClient(result_json(helmet={'status': 'pass', 'confidence': 2, 'evidence': ''}))).analyze_frame(b'jpg')

    def test_result_is_safe_dictionary(self):
        result = VisionAnalysisService(FakeClient(result_json())).analyze_frame(b'jpg').as_dict()
        self.assertEqual(result['helmet']['status'], 'pass')
        self.assertNotIn('api_key', result)


if __name__ == '__main__': unittest.main()
