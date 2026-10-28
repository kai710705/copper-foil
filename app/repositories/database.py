import sqlite3
from flask import current_app, g
from werkzeug.security import generate_password_hash
from .migrations import check_integrity, backup_database, apply_migrations, MIGRATIONS

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user', approval_status TEXT NOT NULL DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, location TEXT NOT NULL, capacity INTEGER NOT NULL, description TEXT DEFAULT '', active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT NOT NULL, start_at TEXT NOT NULL, end_at TEXT NOT NULL, booking_type TEXT NOT NULL DEFAULT 'personal', room_id INTEGER, status TEXT NOT NULL DEFAULT 'confirmed', notes TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(room_id) REFERENCES rooms(id));
CREATE TABLE IF NOT EXISTS safety_alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, area TEXT NOT NULL, alert_type TEXT NOT NULL, severity TEXT NOT NULL DEFAULT 'medium', status TEXT NOT NULL DEFAULT 'open', detected_at TEXT DEFAULT CURRENT_TIMESTAMP, description TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS audits (id INTEGER PRIMARY KEY AUTOINCREMENT, area TEXT NOT NULL, inspector TEXT NOT NULL, issue TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open', due_date TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS inspection_records (id INTEGER PRIMARY KEY AUTOINCREMENT, captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, camera_id INTEGER NOT NULL DEFAULT 0, frame_sequence INTEGER NOT NULL DEFAULT 0, result TEXT NOT NULL CHECK(result IN ('pass','fail','uncertain')), defect_type TEXT NOT NULL DEFAULT '', confidence REAL NOT NULL DEFAULT 0, detections_json TEXT NOT NULL DEFAULT '[]', image_path TEXT NOT NULL DEFAULT '', model_version TEXT NOT NULL DEFAULT '', review_status TEXT NOT NULL DEFAULT 'pending' CHECK(review_status IN ('pending','discarded','false_positive','reinspect')), reviewed_at TEXT, reviewer_id INTEGER REFERENCES users(id));
CREATE INDEX IF NOT EXISTS idx_inspections_review ON inspection_records(review_status,captured_at);
CREATE INDEX IF NOT EXISTS idx_inspections_captured ON inspection_records(captured_at);
"""
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db
def close_db(_=None):
    db = g.pop('db', None)
    if db: db.close()
def init_db(app):
    with app.app_context():
        db = get_db()
        check_integrity(db)
        has_tables = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
        tracked = db.execute("SELECT 1 FROM sqlite_master WHERE name='schema_migrations'").fetchone()
        versions = {r[0] for r in db.execute('SELECT version FROM schema_migrations')} if tracked else set()
        if has_tables and any(version not in versions for version, _ in MIGRATIONS):
            backup_database(db, app.config['DATABASE'])
        db.executescript(SCHEMA)
        inspection_columns = {r['name'] for r in db.execute('PRAGMA table_info(inspection_records)').fetchall()}
        if 'annotated_image_path' not in inspection_columns:
            db.execute("ALTER TABLE inspection_records ADD COLUMN annotated_image_path TEXT NOT NULL DEFAULT ''")
        if 'human_annotations_json' not in inspection_columns:
            db.execute("ALTER TABLE inspection_records ADD COLUMN human_annotations_json TEXT NOT NULL DEFAULT '[]'")
        if 'annotation_status' not in inspection_columns:
            db.execute("ALTER TABLE inspection_records ADD COLUMN annotation_status TEXT NOT NULL DEFAULT 'pending'")
        columns = {r['name'] for r in db.execute('PRAGMA table_info(users)').fetchall()}
        if 'approval_status' not in columns:
            db.execute("ALTER TABLE users ADD COLUMN approval_status TEXT NOT NULL DEFAULT 'pending'")
        db.commit()
        steps = [(version, seed_initial if version == 3 and not has_tables else operation) for version, operation in MIGRATIONS]
        apply_migrations(db, steps)


def seed_initial(db):
    """僅首次建立資料庫時產生示範資料，與版本標記同一交易。"""
    db.execute('INSERT INTO users(username,email,password_hash,role,approval_status,must_change_password) VALUES(?,?,?,?,?,?)', ('admin','admin@tnu.edu.tw',generate_password_hash('admin@123'),'admin','approved',1))
    db.executemany('INSERT INTO rooms(name,location,capacity,description) VALUES(?,?,?,?)', [('第一會議室','行政大樓 3F',20,'適合正式會議'),('創新教室','圖資大樓 2F',40,'附投影與白板'),('多功能廳','活動中心 1F',120,'大型活動空間')])
    db.executemany('INSERT INTO safety_alerts(title,area,alert_type,severity,description) VALUES(?,?,?,?,?)', [('未佩戴護目鏡','化學實驗室 A','個人防護','high','示範警示，尚未接入影像辨識'),('煙霧濃度偏高','材料實驗室 B','環境異常','medium','示範警示，尚未接入感測器')])
    db.execute('INSERT INTO audits(area,inspector,issue,due_date) VALUES(?,?,?,?)', ('化學實驗室 A','王稽核員','化學品標示需補強','2026-10-15'))
    db.executemany('INSERT INTO laboratories(name,location) VALUES(?,?)',[('化學實驗室 A','實驗大樓 1F'),('材料實驗室 B','實驗大樓 2F'),('機械加工區','工場'),('走廊入口','實驗大樓入口')])
