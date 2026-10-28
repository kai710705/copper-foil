from .database import get_db
class BookingRepository:
    @staticmethod
    def list_for_user(uid): return get_db().execute('SELECT b.*,r.name room_name,u.username FROM bookings b LEFT JOIN rooms r ON b.room_id=r.id JOIN users u ON b.user_id=u.id WHERE b.user_id=? OR b.status=? ORDER BY b.start_at',(uid,'approved')).fetchall()
    @staticmethod
    def all(): return get_db().execute('SELECT b.*,r.name room_name,u.username FROM bookings b LEFT JOIN rooms r ON b.room_id=r.id JOIN users u ON b.user_id=u.id ORDER BY b.created_at DESC').fetchall()
    @staticmethod
    def create(uid,title,start,end,kind,room,notes,status):
        db=get_db(); db.execute('INSERT INTO bookings(user_id,title,start_at,end_at,booking_type,room_id,notes,status) VALUES(?,?,?,?,?,?,?,?)',(uid,title,start,end,kind,room or None,notes,status)); db.commit()
    @staticmethod
    def set_status(bid,status): get_db().execute('UPDATE bookings SET status=? WHERE id=?',(status,bid)); get_db().commit()
    @staticmethod
    def delete(bid,uid): get_db().execute('DELETE FROM bookings WHERE id=? AND user_id=?',(bid,uid)); get_db().commit()
    @staticmethod
    def stats():
        db=get_db(); return {'total':db.execute('SELECT COUNT(*) c FROM bookings').fetchone()['c'],'pending':db.execute("SELECT COUNT(*) c FROM bookings WHERE status='pending'").fetchone()['c'],'rooms':db.execute('SELECT COUNT(*) c FROM rooms WHERE active=1').fetchone()['c'],'members':db.execute('SELECT COUNT(*) c FROM users').fetchone()['c']}
