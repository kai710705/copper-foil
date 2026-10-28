"""依影像辨識結果管理工安警訊。"""
from ..repositories.safety_alert_repository import SafetyAlertRepository


class SafetyAlertService:
    def __init__(self, repository=SafetyAlertRepository, model_name=''):
        self.repository = repository
        self.model_name = model_name

    def process(self, source_camera_id, result, area='未指定場所'):
        alerts = []
        for check in ('helmet', 'vest', 'barrier'):
            if getattr(result, check).status != 'fail':
                continue
            existing = self.repository.find_open(source_camera_id, f'ai_{check}')
            row = (self.repository.update_observation(existing['id'], result, check)
                   if existing else self.repository.create(source_camera_id, check, result, self.model_name, area))
            alerts.append(dict(row))
        return alerts
