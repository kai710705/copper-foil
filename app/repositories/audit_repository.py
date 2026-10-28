from .database import get_db

class AuditRepository:
    @staticmethod
    def by_id(aid):return get_db().execute('SELECT * FROM audits WHERE id=?',(aid,)).fetchone()
    @staticmethod
    def create(data,actor):
        db=get_db()
        with db:
            cursor=db.execute('INSERT INTO audits(area,inspector,issue,due_date,laboratory_id,inspector_id) VALUES(?,?,?,?,?,?)',(data['area'],data['inspector'],data['issue'],data['due_date'],data.get('laboratory_id'),actor))
        return dict(AuditRepository.by_id(cursor.lastrowid))
    @staticmethod
    def complete(aid):
        db=get_db()
        with db:db.execute("UPDATE audits SET status='completed' WHERE id=?",(aid,))
        return dict(AuditRepository.by_id(aid))
