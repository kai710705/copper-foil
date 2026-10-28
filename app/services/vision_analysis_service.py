"""工業安全影像辨識與模型輸出驗證。"""
import json
from dataclasses import dataclass

from .ollama_client import OllamaClientError


CHECKS = ('helmet', 'vest', 'barrier')
STATUSES = ('pass', 'fail', 'unknown')


class VisionValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SafetyCheck:
    status: str
    confidence: float
    evidence: str


@dataclass(frozen=True)
class VisionResult:
    helmet: SafetyCheck
    vest: SafetyCheck
    barrier: SafetyCheck
    risk_level: str
    summary: str

    def as_dict(self):
        return {
            name: {'status': getattr(self, name).status,
                   'confidence': getattr(self, name).confidence,
                   'evidence': getattr(self, name).evidence}
            for name in CHECKS
        } | {'risk_level': self.risk_level, 'summary': self.summary}


class VisionAnalysisService:
    PROMPT = (
        '請檢查影像中的工業安全：安全帽、反光背心、場所邊界圍籬。'
        '只回傳 JSON，欄位為 helmet、vest、barrier、risk_level、summary；'
        '每項檢核包含 status(pass/fail/unknown)、confidence(0到1)、evidence。'
        '看不清楚或影像未涵蓋範圍時必須使用 unknown。'
    )

    def __init__(self, ollama_client, camera=None):
        self.ollama_client = ollama_client
        self.camera = camera

    def analyze_frame(self, image_bytes):
        if not image_bytes:
            raise VisionValidationError('沒有可供辨識的影像')
        raw = self.ollama_client.analyze(image_bytes, self.PROMPT)
        return self.validate_result(raw)

    def analyze_camera(self, owner):
        if self.camera is None:
            raise VisionValidationError('鏡頭服務尚未設定')
        frame = self.camera.latest_frame(owner)
        return self.analyze_frame(frame)

    @staticmethod
    def validate_result(raw):
        if not isinstance(raw, str):
            raise VisionValidationError('影像辨識結果格式無效')
        try:
            data = json.loads(raw.strip().removeprefix('```json').removesuffix('```').strip())
        except json.JSONDecodeError as exc:
            raise VisionValidationError('影像辨識結果不是有效 JSON') from exc
        if not isinstance(data, dict):
            raise VisionValidationError('影像辨識結果格式無效')
        checks = {}
        for name in CHECKS:
            value = data.get(name)
            if not isinstance(value, dict) or value.get('status') not in STATUSES:
                raise VisionValidationError(f'{name} 檢核狀態無效')
            confidence = value.get('confidence')
            if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
                raise VisionValidationError(f'{name} 信心分數無效')
            evidence = value.get('evidence', '')
            if not isinstance(evidence, str):
                raise VisionValidationError(f'{name} 判定依據無效')
            checks[name] = SafetyCheck(value['status'], float(confidence), evidence)
        summary = data.get('summary', '')
        risk_level = data.get('risk_level', 'unknown')
        if not isinstance(summary, str) or not isinstance(risk_level, str):
            raise VisionValidationError('影像辨識摘要格式無效')
        return VisionResult(**checks, risk_level=risk_level, summary=summary)
