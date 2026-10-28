import os
from flask import Flask
from .config import load_environment, settings
from .repositories.database import init_db, close_db
from .controllers.mvc import mvc_bp
from .controllers.api import api_bp
from .controllers.video import video_bp
from .services.camera_service import CameraService
from .services.ollama_client import OllamaClient
from .services.vision_analysis_service import VisionAnalysisService
from .services.safety_alert_service import SafetyAlertService
from .repositories.inspection_repository import InspectionRepository
from .services.copper_foil_inspection_service import CopperFoilInspectionService
from .services.inspection_training_export_service import InspectionTrainingExportService
from .controllers.security import configure_security

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    load_environment(os.path.dirname(app.root_path))
    app.config.from_mapping(**settings(app.instance_path))
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(app.config['DATABASE'])), exist_ok=True)
    app.teardown_appcontext(close_db)
    init_db(app)
    app.register_blueprint(mvc_bp)
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    app.extensions['camera'] = CameraService(index=int(os.getenv('CAMERA_INDEX', '0')))
    app.extensions['vision'] = VisionAnalysisService(
        OllamaClient(app.config['OLLAMA_BASE_URL'], app.config['OLLAMA_API_KEY'],
                     app.config['OLLAMA_MODEL'], app.config['OLLAMA_TIMEOUT_SECONDS'],
                     app.config['OLLAMA_MAX_IMAGE_BYTES']),
        app.extensions['camera'])
    app.extensions['safety_alerts'] = SafetyAlertService(model_name=app.config['OLLAMA_MODEL'])
    app.extensions['inspections'] = InspectionRepository()
    app.extensions['inspection_training_export'] = InspectionTrainingExportService(app.extensions['inspections'])
    app.extensions['copper_foil'] = CopperFoilInspectionService(
        app.extensions['camera'], app.extensions['inspections'],
        app.config['YOLO_MODEL_PATH'], app.config['INSPECTION_IMAGE_DIR'])
    app.register_blueprint(video_bp)
    configure_security(app)
    return app
