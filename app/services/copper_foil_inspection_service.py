import os
import cv2
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from .errors import DomainError


class InspectionUnavailableError(DomainError):
    def __init__(self, message):
        super().__init__(message, code='INSPECTION_UNAVAILABLE', status=503)


class CopperFoilInspectionService:
    def __init__(self, camera, repository, model_path, image_dir):
        self.camera = camera
        self.repository = repository
        self.model_path = model_path
        self.image_dir = Path(image_dir)
        self.model = None

    def _load_model(self):
        if not self.model_path:
            raise InspectionUnavailableError('尚未設定 YOLOv8 模型，請設定 YOLO_MODEL_PATH')
        if not os.path.isfile(self.model_path):
            raise InspectionUnavailableError('找不到 YOLOv8 模型檔案，請確認 YOLO_MODEL_PATH')
        if self.model is None:
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.model_path)
            except Exception as exc:
                raise InspectionUnavailableError('YOLOv8 模型無法載入，請確認 ultralytics 與模型檔案') from exc
        return self.model

    def analyze_camera(self, owner):
        model = self._load_model()
        image_bytes = self.camera.latest_frame(owner)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        image_path = self.image_dir / f'{stamp}.jpg'
        image_path.write_bytes(image_bytes)
        image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        try:
            result = model(image, verbose=False)[0]
            detections = []
            for box in result.boxes:
                confidence = float(box.conf[0])
                cls = int(box.cls[0])
                names = result.names
                detections.append({'defect_type': names.get(cls, str(cls)), 'confidence': round(confidence, 4),
                                   'box': [round(float(x), 2) for x in box.xyxy[0].tolist()]})
        except Exception as exc:
            raise InspectionUnavailableError('YOLOv8 影像分析失敗，請檢查模型與影像格式') from exc
        result_name = 'fail' if detections else 'pass'
        max_confidence = max((item['confidence'] for item in detections), default=1.0)
        annotated = image.copy()
        for item in detections:
            x1, y1, x2, y2 = [int(value) for value in item['box']]
            label = f"{item['defect_type']} {item['confidence']:.2f}"
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 38, 255), 3)
            cv2.rectangle(annotated, (x1, max(0, y1 - 28)), (x1 + max(120, len(label) * 9), y1), (0, 38, 255), -1)
            cv2.putText(annotated, label, (x1 + 5, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        annotated_path = self.image_dir / f'{stamp}_annotated.jpg'
        if not cv2.imwrite(str(annotated_path), annotated):
            raise InspectionUnavailableError('標註影像儲存失敗，請檢查影像資料夾權限')
        return self.repository.create({'camera_id': self.camera.index, 'frame_sequence': self.camera.frames,
            'result': result_name, 'defect_type': ', '.join(sorted({item['defect_type'] for item in detections})),
            'confidence': max_confidence, 'detections': detections, 'image_path': str(image_path),
            'model_version': Path(self.model_path).name, 'annotated_image_path': str(annotated_path)})
