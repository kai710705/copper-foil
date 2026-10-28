from .database import get_db

class ResourceRepository:
    fields={'laboratories':('name','location','active'),'cameras':('name','laboratory_id','device_index','active')}
    @classmethod
    def list(cls,kind,active_only=False):
        if kind not in cls.fields:raise ValueError('未知資源')
        if kind=='cameras' and active_only:
            return get_db().execute('SELECT c.* FROM cameras c JOIN laboratories l ON c.laboratory_id=l.id WHERE c.active=1 AND l.active=1 ORDER BY c.id').fetchall()
        return get_db().execute(f'SELECT * FROM {kind}'+(' WHERE active=1' if active_only else '')+' ORDER BY id').fetchall()
    @classmethod
    def by_id(cls,kind,rid):
        if kind not in cls.fields:raise ValueError('未知資源')
        return get_db().execute(f'SELECT * FROM {kind} WHERE id=?',(rid,)).fetchone()
    @classmethod
    def save(cls,kind,data,rid=None):
        fields=cls.fields[kind]
        values=tuple(data[f] for f in fields)
        db=get_db()
        with db:
            if rid is None:
                cursor=db.execute(f'INSERT INTO {kind}({",".join(fields)}) VALUES({",".join("?" for _ in fields)})',values)
                rid=cursor.lastrowid
            else:
                db.execute(f'UPDATE {kind} SET {",".join(f+"=?" for f in fields)} WHERE id=?',values+(rid,))
        return dict(cls.by_id(kind,rid))
