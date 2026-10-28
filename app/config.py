"""環境變數與本機 .env 設定載入。"""
import os
import secrets
from pathlib import Path


def load_environment(project_root):
    """讀取 .env 範例格式，保留作業系統已設定的環境變數。"""
    env_file = Path(project_root) / '.env'
    if not env_file.is_file():
        return
    for raw_line in env_file.read_text(encoding='utf-8-sig').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key, value = key.strip(), value.strip()
        if value[:1] == value[-1:] and value.startswith(('"', "'")):
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def settings(instance_path):
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key and os.getenv('APP_ENV', 'development').lower() == 'production':
        raise RuntimeError('正式環境必須設定 SECRET_KEY。')
    return {
        'SECRET_KEY': secret_key or secrets.token_urlsafe(48),
        'DATABASE': os.getenv('DATABASE', os.path.join(instance_path, 'calendar.sqlite')),
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'SESSION_COOKIE_SECURE': os.getenv('SESSION_COOKIE_SECURE', '0') == '1',
        'OLLAMA_BASE_URL': os.getenv('OLLAMA_BASE_URL', ''),
        'OLLAMA_API_KEY': os.getenv('OLLAMA_API_KEY', ''),
        'OLLAMA_MODEL': os.getenv('OLLAMA_MODEL', 'gemma4:31b-cloud'),
        'OLLAMA_TIMEOUT_SECONDS': float(os.getenv('OLLAMA_TIMEOUT_SECONDS', '30')),
        'OLLAMA_MAX_IMAGE_BYTES': int(os.getenv('OLLAMA_MAX_IMAGE_BYTES', str(4 * 1024 * 1024))),
        'YOLO_MODEL_PATH': os.getenv('YOLO_MODEL_PATH', ''),
        'INSPECTION_IMAGE_DIR': os.getenv('INSPECTION_IMAGE_DIR', os.path.join(instance_path, 'inspections')),
    }
