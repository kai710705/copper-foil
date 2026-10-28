from .database import get_db
from contextlib import contextmanager
class UserRepository:
    @staticmethod
    def by_username(username): return get_db().execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
    @staticmethod
    def by_id(uid): return get_db().execute('SELECT id,username,email,role,approval_status,must_change_password FROM users WHERE id=?',(uid,)).fetchone()
    @staticmethod
    def credentials(uid):return get_db().execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
    @staticmethod
    def change_password(uid,password_hash):
        db=get_db()
        with db:db.execute('UPDATE users SET password_hash=?,must_change_password=0 WHERE id=?',(password_hash,uid))
    @staticmethod
    def all(status=None):
        sql='SELECT id,username,email,role,approval_status,created_at FROM users'
        return get_db().execute(sql+(' WHERE approval_status=?' if status else '')+' ORDER BY id DESC',(status,) if status else ()).fetchall()
    @staticmethod
    def create(username,email,password_hash,role='user'):
        db=get_db()
        with db:
            db.execute('INSERT INTO users(username,email,password_hash,role,approval_status) VALUES(?,?,?,?,?)',(username,email,password_hash,role,'pending'))
    @staticmethod
    def set_status(uid,status):
        db=get_db(); db.execute('UPDATE users SET approval_status=? WHERE id=?',(status,uid)); db.commit()
    @staticmethod
    @contextmanager
    def transaction():
        db=get_db()
        try:
            db.execute('BEGIN IMMEDIATE')
            yield
            db.commit()
        except Exception:
            db.rollback()
            raise
    @staticmethod
    def approved_admin_count():
        return get_db().execute("SELECT COUNT(*) FROM users WHERE role='admin' AND approval_status='approved'").fetchone()[0]
    @staticmethod
    def review(uid,actor,previous,status):
        db=get_db()
        db.execute('UPDATE users SET approval_status=? WHERE id=?',(status,uid))
        db.execute('INSERT INTO member_review_history(user_id,actor_id,from_status,to_status) VALUES(?,?,?,?)',(uid,actor,previous,status))
    @staticmethod
    def history(uid):
        return get_db().execute('SELECT h.*,u.username actor_name FROM member_review_history h JOIN users u ON u.id=h.actor_id WHERE h.user_id=? ORDER BY h.id DESC',(uid,)).fetchall()
