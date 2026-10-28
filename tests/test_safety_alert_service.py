import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.safety_alert_service import SafetyAlertService
from app.services.vision_analysis_service import VisionAnalysisService
from tests.test_vision_analysis_service import FakeClient, result_json


class FakeRepository:
    rows = []
    @classmethod
    def find_open(cls, camera, alert_type):
        return next((row for row in cls.rows if row['source_camera_id'] == camera and row['alert_type'] == alert_type and row['status'] == 'open'), None)
    @classmethod
    def create(cls, camera, check, result, model, area):
        row={'id':len(cls.rows)+1,'source_camera_id':camera,'alert_type':f'ai_{check}','status':'open'}
        cls.rows.append(row)
        return row
    @classmethod
    def update_observation(cls, alert_id, result, check):
        return next(row for row in cls.rows if row['id'] == alert_id)


class SafetyAlertServiceTests(unittest.TestCase):
    def setUp(self): FakeRepository.rows=[]
    def test_only_fail_creates_and_repeated_failure_deduplicates(self):
        result=VisionAnalysisService(FakeClient(result_json())).analyze_frame(b'jpg')
        service=SafetyAlertService(FakeRepository, 'gemma4')
        self.assertEqual(len(service.process(0,result)), 1)
        self.assertEqual(len(service.process(0,result)), 1)
        self.assertEqual(len(FakeRepository.rows), 1)
    def test_pass_and_unknown_create_no_alert(self):
        result=VisionAnalysisService(FakeClient(result_json(
            helmet={'status':'pass','confidence':.9,'evidence':'ok'},
            vest={'status':'unknown','confidence':.4,'evidence':'unclear'},
            barrier={'status':'pass','confidence':.9,'evidence':'ok'}))).analyze_frame(b'jpg')
        self.assertEqual(SafetyAlertService(FakeRepository).process(0,result), [])


if __name__ == '__main__': unittest.main()
