from .database import get_db
from .safety_alert_repository import now_utc

class MonitoringRepository:
    @staticmethod
    def snapshot():
        db=get_db()
        def count(sql):return db.execute(sql).fetchone()[0]
        return {'alerts':[dict(r) for r in db.execute('SELECT * FROM safety_alerts ORDER BY detected_at DESC,id DESC')],
                'audits':[dict(r) for r in db.execute('SELECT * FROM audits ORDER BY created_at DESC,id DESC')],
                'stats':{'alerts':count("SELECT COUNT(*) FROM safety_alerts WHERE status='open'"),
                         'audits':count("SELECT COUNT(*) FROM audits WHERE status='open'"),
                         'cameras':count('SELECT COUNT(*) FROM cameras c JOIN laboratories l ON c.laboratory_id=l.id WHERE c.active=1 AND l.active=1'),
                         'members':count('SELECT COUNT(*) FROM users'),
                         'pending_members':count("SELECT COUNT(*) FROM users WHERE approval_status='pending'"),
                         'laboratories':count('SELECT COUNT(*) FROM laboratories WHERE active=1'),
                         'safe_rate':94,'safe_rate_demo':True}}
    @staticmethod
    def alert(aid):return get_db().execute('SELECT * FROM safety_alerts WHERE id=?',(aid,)).fetchone()
    @staticmethod
    def resolve_alert(aid,actor):
        db=get_db()
        with db:db.execute("UPDATE safety_alerts SET status='resolved',handler_id=?,resolved_at=? WHERE id=?",(actor,now_utc(),aid))
