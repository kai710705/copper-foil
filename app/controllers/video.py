"""鏡頭頁面與 API：身分檢查、CSRF 驗證與串流回應。"""
import secrets
from flask import Blueprint, current_app, session, request, jsonify, render_template, redirect, Response, send_file
from pathlib import Path
from ..services.camera_service import CameraBusyError, CameraError
from ..services.camera_auth_service import CameraAuthService
from ..services.ollama_client import OllamaClientError
from ..services.vision_analysis_service import VisionValidationError
from ..services.copper_foil_inspection_service import InspectionUnavailableError
from .security import csrf_token

video_bp = Blueprint('video', __name__)

def error(code, message, status):
    return jsonify(error={'code': code, 'message': message, 'details': None}), status

@video_bp.before_request
def authorize():
    if not CameraAuthService.approved(session.get('user_id')):
        return redirect('/login') if request.path == '/video' else error('UNAUTHORIZED', '請使用已核准帳號登入', 401)

@video_bp.get('/video')
def page():
    return render_template('video.html', csrf=csrf_token())

@video_bp.get('/inspections/pending')
def pending_page():
    return render_template('inspection_pending.html', csrf=csrf_token())

@video_bp.get('/inspections/<int:inspection_id>/annotate')
def annotate_page(inspection_id):
    if not current_app.extensions['inspections'].get(inspection_id):
        return error('NOT_FOUND', '找不到檢測紀錄', 404)
    return render_template('inspection_annotate.html', inspection_id=inspection_id, csrf=csrf_token())

@video_bp.get('/api/v1/camera/status')
def status():
    return jsonify(data=current_app.extensions['camera'].status(session['user_id']))

@video_bp.post('/api/v1/camera/start')
def start():
    try:
        return jsonify(data=current_app.extensions['camera'].start(session['user_id']))
    except CameraBusyError as exc:
        return error('CAMERA_BUSY', str(exc), 409)
    except CameraError as exc:
        return error('CAMERA_UNAVAILABLE', str(exc), 503)

@video_bp.post('/api/v1/camera/stop')
def stop():
    try:
        return jsonify(data=current_app.extensions['camera'].stop(session['user_id']))
    except CameraError as exc:
        return error('FORBIDDEN', str(exc), 403)

@video_bp.get('/api/v1/camera/stream')
def stream():
    camera = current_app.extensions['camera']
    state = camera.status(session['user_id'])
    if not state['can_control'] or state['state'] not in ('starting', 'streaming'):
        return error('CAMERA_INACTIVE', '請先按啟動鏡頭', 409)
    return Response(camera.stream(session['user_id']), mimetype='multipart/x-mixed-replace; boundary=frame', headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})

@video_bp.post('/api/v1/vision/analyze')
def analyze():
    try:
        result = current_app.extensions['vision'].analyze_camera(session['user_id'])
        alerts = current_app.extensions['safety_alerts'].process(
            current_app.extensions['camera'].index, result)
        return jsonify(data={'analysis': result.as_dict(), 'alerts': alerts})
    except VisionValidationError as exc:
        return error('VISION_VALIDATION', str(exc), 400)
    except CameraError as exc:
        return error('CAMERA_INACTIVE', str(exc), 409)
    except OllamaClientError as exc:
        return error('VISION_UNAVAILABLE', str(exc), 503)

@video_bp.post('/api/v1/inspections/analyze')
def analyze_copper_foil():
    try:
        record = current_app.extensions['copper_foil'].analyze_camera(session['user_id'])
        return jsonify(data=record), 201
    except CameraError as exc:
        return error('CAMERA_INACTIVE', str(exc), 409)
    except InspectionUnavailableError as exc:
        return error('INSPECTION_UNAVAILABLE', str(exc), 503)

@video_bp.get('/api/v1/inspections')
def inspections():
    pending = request.args.get('pending') == '1'
    return jsonify(data=current_app.extensions['inspections'].list(pending_only=pending))

@video_bp.get('/api/v1/inspections/stats')
def inspection_stats():
    return jsonify(data=current_app.extensions['inspections'].stats())

@video_bp.patch('/api/v1/inspections/<int:inspection_id>/review')
def review_inspection(inspection_id):
    payload = request.get_json(silent=True) or {}
    status = payload.get('status')
    if status not in ('discarded', 'false_positive', 'reinspect'):
        return error('VALIDATION', '處理狀態必須是 discarded、false_positive 或 reinspect', 400)
    record = current_app.extensions['inspections'].review(inspection_id, status, session['user_id'])
    if not record:
        return error('NOT_FOUND', '找不到待處理的檢測紀錄，或紀錄已處理', 404)
    return jsonify(data=record)

@video_bp.get('/api/v1/inspections/<int:inspection_id>/image')
def inspection_image(inspection_id):
    record = current_app.extensions['inspections'].get(inspection_id)
    if not record or not (record['annotated_image_path'] or record['image_path']):
        return error('NOT_FOUND', '找不到檢測影像', 404)
    image_root = Path(current_app.config['INSPECTION_IMAGE_DIR']).resolve()
    source = request.args.get('source', 'annotated')
    image_path = Path(record['image_path'] if source == 'original' else (record['annotated_image_path'] or record['image_path'])).resolve()
    if image_root not in image_path.parents or not image_path.is_file():
        return error('NOT_FOUND', '找不到檢測影像', 404)
    return send_file(image_path, mimetype='image/jpeg', max_age=0)

@video_bp.patch('/api/v1/inspections/<int:inspection_id>/annotations')
def save_annotations(inspection_id):
    payload = request.get_json(silent=True) or {}
    annotations = payload.get('annotations')
    if not isinstance(annotations, list) or any(not isinstance(item, dict) for item in annotations):
        return error('VALIDATION', '標註格式無效', 400)
    for item in annotations:
        if item.get('defect_type') not in ('punching','welding_line','crescent_gap','water_spot','oil_spot','silk_spot','inclusion','rolled_pit','crease','waist_fold'):
            return error('VALIDATION', '瑕疵類型無效', 400)
        box = item.get('box')
        if not isinstance(box, list) or len(box) != 4 or any(not isinstance(value, (int, float)) for value in box):
            return error('VALIDATION', '瑕疵框座標無效', 400)
    record = current_app.extensions['inspections'].save_annotations(inspection_id, annotations)
    if not record:
        return error('NOT_FOUND', '找不到檢測紀錄', 404)
    return jsonify(data=record)

@video_bp.get('/api/v1/inspections/training-export')
def training_export():
    archive = current_app.extensions['inspection_training_export'].build_zip()
    return send_file(archive, mimetype='application/zip', as_attachment=True,
                     download_name='copper_foil_training_data.zip')
