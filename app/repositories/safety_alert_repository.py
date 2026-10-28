"""AI 工安警訊的資料存取。"""
import json
from datetime import datetime, timezone

from .database import get_db


def now_utc():
    return datetime.now(timezone.utc).isoformat()


class SafetyAlertRepository:
    @staticmethod
    def find_open(source_camera_id, alert_type):
        return get_db().execute(
            "SELECT * FROM safety_alerts WHERE source_camera_id=? AND alert_type=? AND status='open' ORDER BY id DESC LIMIT 1",
            (source_camera_id, alert_type)).fetchone()

    @staticmethod
    def create(source_camera_id, check, result, model_name, area='未指定場所'):
        db = get_db()
        observed = now_utc()
        title = {'helmet': '未佩戴安全帽', 'vest': '未穿反光背心', 'barrier': '場所未設置圍籬'}[check]
        value = getattr(result, check)
        payload = json.dumps(result.as_dict(), ensure_ascii=False)
        with db:
            cursor = db.execute(
                """INSERT INTO safety_alerts
                (title,area,alert_type,severity,status,detected_at,description,source_camera_id,analysis_json,model_name,
                 helmet_status,vest_status,barrier_status,helmet_confidence,vest_confidence,barrier_confidence,last_observed_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (title, area, f'ai_{check}', 'high', 'open', observed, value.evidence,
                 source_camera_id, payload, model_name, result.helmet.status, result.vest.status,
                 result.barrier.status, result.helmet.confidence, result.vest.confidence,
                 result.barrier.confidence, observed))
        return SafetyAlertRepository.get(cursor.lastrowid)

    @staticmethod
    def update_observation(alert_id, result, check):
        db = get_db()
        observed = now_utc()
        value = getattr(result, check)
        with db:
            db.execute("""UPDATE safety_alerts SET description=?, analysis_json=?, helmet_status=?, vest_status=?,
                barrier_status=?, helmet_confidence=?, vest_confidence=?, barrier_confidence=?, last_observed_at=? WHERE id=?""",
                       (value.evidence, json.dumps(result.as_dict(), ensure_ascii=False), result.helmet.status,
                        result.vest.status, result.barrier.status, result.helmet.confidence,
                        result.vest.confidence, result.barrier.confidence, observed, alert_id))
        return SafetyAlertRepository.get(alert_id)

    @staticmethod
    def get(alert_id):
        return get_db().execute('SELECT * FROM safety_alerts WHERE id=?', (alert_id,)).fetchone()

    @staticmethod
    def list_open():
        return get_db().execute("SELECT * FROM safety_alerts WHERE status='open' ORDER BY detected_at DESC,id DESC").fetchall()

    @staticmethod
    def resolve(alert_id, handler_id):
        with get_db():
            get_db().execute("UPDATE safety_alerts SET status='resolved',handler_id=? WHERE id=?", (handler_id, alert_id))
