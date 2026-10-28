import json
from datetime import datetime, timezone
from .database import get_db


class InspectionRepository:
    def create(self, record):
        db = get_db()
        cursor = db.execute('''INSERT INTO inspection_records
            (camera_id,frame_sequence,result,defect_type,confidence,detections_json,image_path,annotated_image_path,model_version)
            VALUES(?,?,?,?,?,?,?,?,?)''', (record['camera_id'], record['frame_sequence'], record['result'],
            record['defect_type'], record['confidence'], json.dumps(record['detections'], ensure_ascii=False),
            record['image_path'], record['annotated_image_path'], record['model_version']))
        db.commit()
        return self.get(cursor.lastrowid)

    def list(self, pending_only=False, limit=100):
        sql = 'SELECT * FROM inspection_records'
        params = []
        if pending_only:
            sql += " WHERE review_status='pending'"
        rows = get_db().execute(sql + ' ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
        return [self._map(row) for row in rows]

    def reviewed(self):
        rows = get_db().execute("SELECT * FROM inspection_records WHERE review_status != 'pending' ORDER BY id").fetchall()
        return [self._map(row) for row in rows]

    def stats(self):
        db = get_db()
        today = db.execute("SELECT COUNT(*) FROM inspection_records WHERE date(captured_at)=date('now','localtime')").fetchone()[0]
        defects = db.execute("SELECT COUNT(*) FROM inspection_records WHERE date(captured_at)=date('now','localtime') AND result='fail'").fetchone()[0]
        pending = db.execute("SELECT COUNT(*) FROM inspection_records WHERE review_status='pending'").fetchone()[0]
        return {'today_inspections': today, 'today_defects': defects, 'pending_reviews': pending}

    def get(self, inspection_id):
        row = get_db().execute('SELECT * FROM inspection_records WHERE id=?', (inspection_id,)).fetchone()
        return self._map(row) if row else None

    def review(self, inspection_id, status, reviewer_id):
        now = datetime.now(timezone.utc).isoformat()
        db = get_db()
        cursor = db.execute('UPDATE inspection_records SET review_status=?,reviewed_at=?,reviewer_id=? WHERE id=? AND review_status=?',
                            (status, now, reviewer_id, inspection_id, 'pending'))
        db.commit()
        return self.get(inspection_id) if cursor.rowcount else None

    @staticmethod
    def _map(row):
        if not row:
            return None
        item = dict(row)
        item['detections'] = json.loads(item.pop('detections_json') or '[]')
        item['human_annotations'] = json.loads(item.pop('human_annotations_json', '[]') or '[]')
        return item

    def save_annotations(self, inspection_id, annotations):
        db = get_db()
        cursor = db.execute("UPDATE inspection_records SET human_annotations_json=?, annotation_status='complete' WHERE id=?",
                            (json.dumps(annotations, ensure_ascii=False), inspection_id))
        db.commit()
        return self.get(inspection_id) if cursor.rowcount else None
