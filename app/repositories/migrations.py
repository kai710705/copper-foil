"""SQLite 升級與一致性備份；任何舊外鍵問題均保留資料並中止升級。"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from werkzeug.security import check_password_hash


def monitoring_schema(db):
    columns = {r[1] for r in db.execute('PRAGMA table_info(users)')}
    if 'must_change_password' not in columns:
        db.execute('ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0 CHECK(must_change_password IN (0,1))')
    admin = db.execute("SELECT id,password_hash FROM users WHERE username='admin'").fetchone()
    if admin and check_password_hash(admin[1], 'admin@123'):
        db.execute('UPDATE users SET must_change_password=1 WHERE id=?',(admin[0],))
    statements = [
        "CREATE TABLE IF NOT EXISTS member_review_history (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL REFERENCES users(id),actor_id INTEGER NOT NULL REFERENCES users(id),from_status TEXT NOT NULL,to_status TEXT NOT NULL CHECK(to_status IN ('approved','rejected','disabled')),created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS laboratories (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE,location TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS cameras (id INTEGER PRIMARY KEY AUTOINCREMENT,laboratory_id INTEGER NOT NULL REFERENCES laboratories(id),name TEXT NOT NULL,device_index INTEGER NOT NULL DEFAULT 0 CHECK(device_index>=0),active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)",
        'CREATE INDEX IF NOT EXISTS idx_users_approval ON users(approval_status)',
        'CREATE INDEX IF NOT EXISTS idx_review_user ON member_review_history(user_id,created_at)',
        'CREATE INDEX IF NOT EXISTS idx_cameras_lab ON cameras(laboratory_id)',
        'CREATE INDEX IF NOT EXISTS idx_alerts_status ON safety_alerts(status)',
        'CREATE INDEX IF NOT EXISTS idx_audits_status ON audits(status)',
    ]
    for statement in statements:
        db.execute(statement)
    for table, fields in {
        'safety_alerts': [('laboratory_id','INTEGER REFERENCES laboratories(id)'),('handler_id','INTEGER REFERENCES users(id)')],
        'audits': [('laboratory_id','INTEGER REFERENCES laboratories(id)'),('inspector_id','INTEGER REFERENCES users(id)')],
    }.items():
        existing = {r[1] for r in db.execute(f'PRAGMA table_info({table})')}
        for name, declaration in fields:
            if name not in existing:
                db.execute(f'ALTER TABLE {table} ADD COLUMN {name} {declaration}')


def vision_alert_schema(db):
    fields = {
        'source_camera_id': 'INTEGER',
        'analysis_json': "TEXT NOT NULL DEFAULT '{}'",
        'model_name': "TEXT NOT NULL DEFAULT ''",
        'helmet_status': "TEXT NOT NULL DEFAULT 'unknown'",
        'vest_status': "TEXT NOT NULL DEFAULT 'unknown'",
        'barrier_status': "TEXT NOT NULL DEFAULT 'unknown'",
        'helmet_confidence': 'REAL NOT NULL DEFAULT 0',
        'vest_confidence': 'REAL NOT NULL DEFAULT 0',
        'barrier_confidence': 'REAL NOT NULL DEFAULT 0',
        'last_observed_at': 'TEXT',
        'resolved_at': 'TEXT',
        'handler_id': 'INTEGER REFERENCES users(id)',
    }
    existing = {r[1] for r in db.execute('PRAGMA table_info(safety_alerts)')}
    for name, declaration in fields.items():
        if name not in existing:
            db.execute(f'ALTER TABLE safety_alerts ADD COLUMN {name} {declaration}')
    db.execute('CREATE INDEX IF NOT EXISTS idx_ai_alert_dedupe ON safety_alerts(source_camera_id,alert_type,status)')


def copper_foil_schema(db):
    db.execute("""CREATE TABLE IF NOT EXISTS inspection_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        camera_id INTEGER NOT NULL DEFAULT 0,
        frame_sequence INTEGER NOT NULL DEFAULT 0,
        result TEXT NOT NULL CHECK(result IN ('pass','fail','uncertain')),
        defect_type TEXT NOT NULL DEFAULT '',
        confidence REAL NOT NULL DEFAULT 0,
        detections_json TEXT NOT NULL DEFAULT '[]',
        image_path TEXT NOT NULL DEFAULT '',
        model_version TEXT NOT NULL DEFAULT '',
        review_status TEXT NOT NULL DEFAULT 'pending' CHECK(review_status IN ('pending','discarded','false_positive','reinspect')),
        reviewed_at TEXT,
        reviewer_id INTEGER REFERENCES users(id)
    )""")
    db.execute('CREATE INDEX IF NOT EXISTS idx_inspections_review ON inspection_records(review_status,captured_at)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_inspections_captured ON inspection_records(captured_at)')


MIGRATIONS = [(1, lambda connection: None), (2, monitoring_schema), (3, lambda connection: None), (4, vision_alert_schema)]


def check_integrity(db):
    if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise RuntimeError('資料庫完整性檢查失敗，請先還原或修復備份')
    if db.execute('PRAGMA foreign_key_check').fetchall():
        raise RuntimeError('舊資料存在無效外鍵；升級已停止，資料未刪除')


def backup_database(db, database_path):
    if database_path == ':memory:':
        return None
    path = Path(database_path)
    directory = path.parent / 'backups'
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    target = directory / f'{path.stem}-{stamp}.sqlite'
    destination = sqlite3.connect(target)
    try:
        db.backup(destination)
    finally:
        destination.close()
    baseline = {}
    for row in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        name = row[0]
        # 名稱來自 SQLite 系統目錄，不使用外部輸入。
        quoted = '"' + name.replace('"', '""') + '"'
        baseline[name] = {'sql': row[1], 'rows': db.execute(f'SELECT COUNT(*) FROM {quoted}').fetchone()[0]}
    target.with_suffix('.json').write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding='utf-8')
    return target


def apply_migrations(db, steps=MIGRATIONS):
    db.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
    db.commit()
    for version, operation in steps:
        if db.execute('SELECT 1 FROM schema_migrations WHERE version=?', (version,)).fetchone():
            continue
        try:
            db.execute('BEGIN IMMEDIATE')
            operation(db)
            check_integrity(db)
            db.execute('INSERT INTO schema_migrations(version) VALUES(?)', (version,))
            db.commit()
        except Exception:
            db.rollback()
            raise
