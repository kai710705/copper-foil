"""驗證舊資料、備份、外鍵失敗與升級交易。"""
import sys, sqlite3, tempfile, unittest
from pathlib import Path
from contextlib import contextmanager
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.repositories.database import SCHEMA
from app.repositories.migrations import apply_migrations

@contextmanager
def connection(path):
    db=sqlite3.connect(path)
    try:
        with db:
            yield db
    finally:
        db.close()

class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.path = str(Path(self.tmp.name)/'legacy.sqlite')
    def tearDown(self):
        self.tmp.cleanup()
    def test_legacy_preserved_and_backed_up(self):
        with connection(self.path) as db:
            db.executescript(SCHEMA)
            db.execute("INSERT INTO users(username,email,password_hash,approval_status) VALUES('kept','kept@example.com','keep-hash','approved')")
            db.execute("INSERT INTO bookings(user_id,title,start_at,end_at) VALUES(1,'保留預約','2026-10-06T09:00','2026-10-06T10:00')")
            db.execute("INSERT INTO safety_alerts(title,area,alert_type) VALUES('保留警示','區域','防護')")
            db.execute("INSERT INTO audits(area,inspector,issue) VALUES('區域','人員','保留稽核')")
        create_app({'TESTING':True,'DATABASE':self.path})
        create_app({'TESTING':True,'DATABASE':self.path})
        with connection(self.path) as db:
            self.assertEqual(db.execute("SELECT password_hash FROM users WHERE username='kept'").fetchone()[0],'keep-hash')
            for table in ('bookings','safety_alerts','audits'):
                self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0],1)
        backups=list((Path(self.tmp.name)/'backups').glob('*.sqlite'))
        self.assertEqual(len(backups),1)
        with connection(backups[0]) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM users').fetchone()[0],1)
    def test_orphan_stops_upgrade(self):
        with connection(self.path) as db:
            db.executescript(SCHEMA)
            db.execute("INSERT INTO bookings(user_id,title,start_at,end_at) VALUES(999,'孤兒','a','b')")
        with self.assertRaises(RuntimeError):
            create_app({'TESTING':True,'DATABASE':self.path})
        with connection(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM bookings').fetchone()[0],1)
    def test_failed_migration_rolls_back(self):
        with connection(self.path) as db:
            def broken(connection):
                connection.execute('CREATE TABLE should_rollback(id INTEGER)')
                raise ValueError('模擬升級失敗')
            with self.assertRaises(ValueError):apply_migrations(db,[(99,broken)])
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='should_rollback'").fetchone())
            self.assertEqual(db.execute('SELECT COUNT(*) FROM schema_migrations').fetchone()[0],0)
    def test_new_schema_constraints_and_idempotence(self):
        app=create_app({'TESTING':True,'DATABASE':self.path})
        create_app({'TESTING':True,'DATABASE':self.path})
        with app.app_context():
            from app.repositories.database import get_db
            db=get_db()
            self.assertEqual(db.execute('PRAGMA foreign_keys').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM schema_migrations').fetchone()[0],4)
            self.assertEqual(db.execute("SELECT must_change_password FROM users WHERE username='admin'").fetchone()[0],1)
            for table in ('member_review_history','laboratories','cameras'):
                self.assertTrue(db.execute(f'PRAGMA table_info({table})').fetchall())
            alert_columns={row[1] for row in db.execute('PRAGMA table_info(safety_alerts)')}
            self.assertIn('analysis_json', alert_columns)
            self.assertIn('helmet_confidence', alert_columns)
            self.assertIn('resolved_at', alert_columns)
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO cameras(laboratory_id,name) VALUES(999,'不存在區域')")
            db.rollback()
    def test_seed_once_and_preserve_changed_password(self):
        create_app({'TESTING':True,'DATABASE':self.path})
        with connection(self.path) as db:
            db.execute('DELETE FROM safety_alerts')
            db.execute('DELETE FROM audits')
            db.execute("UPDATE users SET password_hash='changed',must_change_password=0 WHERE username='admin'")
        create_app({'TESTING':True,'DATABASE':self.path})
        with connection(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM safety_alerts').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM audits').fetchone()[0],0)
            self.assertEqual(db.execute("SELECT password_hash FROM users WHERE username='admin'").fetchone()[0],'changed')
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users WHERE username='admin'").fetchone()[0],1)

if __name__=='__main__':unittest.main()
