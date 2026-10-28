from flask import Blueprint, request, jsonify, session
from ..repositories.booking_repository import BookingRepository
from ..repositories.user_repository import UserRepository
from ..services.auth_service import AuthService
from ..services.booking_service import BookingService
from ..repositories.database import get_db
from ..services.errors import DomainError
from .security import csrf_token, establish_login
from ..services.member_service import MemberService
from ..services.resource_service import ResourceService
from ..services.monitoring_service import MonitoringService
from ..services.audit_service import AuditService
api_bp=Blueprint('api',__name__)
def ok(data): return jsonify({'data':data})
@api_bp.get('/auth/csrf')
def csrf():return ok({'csrf_token':csrf_token()})
@api_bp.post('/auth/login')
def login_api():
    data=request.get_json(silent=True)
    if not isinstance(data,dict):raise DomainError('請提供 JSON 物件')
    user=AuthService.login(data.get('username'),data.get('password'))
    if not user:raise DomainError('帳號、密碼或審核狀態不符','UNAUTHORIZED',401)
    establish_login(user)
    return ok({'user':AuthService.current(user['id']),'csrf_token':csrf_token(),'redirect':'/password' if user['must_change_password'] else '/'})
@api_bp.post('/auth/logout')
def logout_api():
    session.clear()
    return ok({'message':'已登出'})
@api_bp.post('/auth/password')
def password_api():
    data=request.get_json(silent=True)
    if not isinstance(data,dict):raise DomainError('請提供 JSON 物件')
    AuthService.change_password(session['user_id'],data.get('current_password'),data.get('password'))
    return ok({'message':'密碼已更新'})
@api_bp.post('/auth/register')
def register_api():
    data=request.get_json(silent=True)
    if not isinstance(data,dict):return jsonify(error={'code':'VALIDATION','message':'請提供 JSON 物件','details':None}),400
    try: AuthService.register(data.get('username'),data.get('email'),data.get('password'),data.get('role','user'))
    except DomainError as exc: return jsonify(error={'code':exc.code,'message':str(exc),'details':None}),exc.status
    return ok({'message':'註冊申請已送出，等待管理者審核'}),201
@api_bp.get('/calendar')
def calendar():
    if not session.get('user_id'): return jsonify({'error':{'code':'UNAUTHORIZED','message':'請先登入'}}),401
    rows=BookingRepository.list_for_user(session['user_id']); return ok([dict(r) for r in rows])
@api_bp.post('/bookings')
def create_booking():
    if not session.get('user_id'): return jsonify({'error':{'code':'UNAUTHORIZED','message':'請先登入'}}),401
    data=request.get_json() or {}
    required=['title','start_at','end_at']
    if any(not data.get(x) for x in required): return jsonify({'error':{'code':'VALIDATION','message':'請填寫完整欄位'}}),400
    BookingService.create(session['user_id'],data); return ok({'message':'Booking 已建立'}),201
@api_bp.delete('/bookings/<int:bid>')
def delete_booking(bid): BookingRepository.delete(bid,session.get('user_id')); return ok({'message':'已刪除'})
@api_bp.get('/rooms')
def rooms(): return ok([dict(r) for r in get_db().execute('SELECT * FROM rooms WHERE active=1')])
@api_bp.get('/monitoring')
def monitoring():
    return ok(MonitoringService.snapshot())
@api_bp.patch('/admin/alerts/<int:aid>')
def alert_update(aid):
    data=request.get_json(silent=True)
    if not isinstance(data,dict):raise DomainError('請提供 JSON 物件')
    return ok(MonitoringService.resolve(session['user_id'],aid,data.get('status')))
@api_bp.post('/admin/audits')
def audit_create():return ok(AuditService.create(session['user_id'],request.get_json(silent=True))),201
@api_bp.patch('/admin/audits/<int:aid>')
def audit_update(aid):
    data=request.get_json(silent=True)
    if not isinstance(data,dict):raise DomainError('請提供 JSON 物件')
    return ok(AuditService.complete(session['user_id'],aid,data.get('status')))
@api_bp.get('/admin/dashboard')
def dashboard():
    return ok(MonitoringService.snapshot())
@api_bp.get('/admin/users')
def users_admin():
    return ok(MemberService.list(session['user_id'],request.args.get('status')))
@api_bp.get('/admin/users/<int:uid>/history')
def user_history(uid):return ok(MemberService.history(session['user_id'],uid))
@api_bp.route('/admin/laboratories',methods=['GET','POST'])
def laboratories_admin():
    if request.method=='GET':return ok(ResourceService.list('laboratories',session['user_id']))
    return ok(ResourceService.save(session['user_id'],'laboratories',request.get_json(silent=True))),201
@api_bp.patch('/admin/laboratories/<int:rid>')
def laboratory_update(rid):return ok(ResourceService.save(session['user_id'],'laboratories',request.get_json(silent=True),rid))
@api_bp.route('/admin/cameras',methods=['GET','POST'])
def cameras_admin():
    if request.method=='GET':return ok(ResourceService.list('cameras',session['user_id']))
    return ok(ResourceService.save(session['user_id'],'cameras',request.get_json(silent=True))),201
@api_bp.patch('/admin/cameras/<int:rid>')
def camera_update(rid):return ok(ResourceService.save(session['user_id'],'cameras',request.get_json(silent=True),rid))
@api_bp.get('/laboratories')
def laboratory_list():return ok(ResourceService.list('laboratories'))
@api_bp.get('/cameras')
def camera_list():return ok(ResourceService.list('cameras'))
@api_bp.patch('/admin/users/<int:uid>')
def review_user(uid):
    data=request.get_json(silent=True)
    if not isinstance(data,dict):raise DomainError('請提供 JSON 物件')
    return ok(MemberService.review(session['user_id'],uid,data.get('approval_status')))
@api_bp.patch('/admin/bookings/<int:bid>')
def review(bid):
    if session.get('role')!='admin': return jsonify({'error':{'code':'FORBIDDEN','message':'需要管理者權限'}}),403
    status=(request.get_json() or {}).get('status');
    if status not in ('approved','rejected'): return jsonify({'error':{'code':'VALIDATION','message':'狀態不正確'}}),400
    BookingRepository.set_status(bid,status); return ok({'message':'審核完成'})
