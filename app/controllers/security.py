"""HTTP 層共用 Session 與 CSRF；業務身分檢查由 AuthService 提供。"""
import secrets
from flask import session, request, g, redirect, jsonify
from ..services.auth_service import AuthService
from ..services.errors import DomainError

def csrf_token():
    if 'csrf_token' not in session:session['csrf_token']=secrets.token_urlsafe(32)
    return session['csrf_token']

def establish_login(user):
    session.clear()
    session['user_id']=user['id']
    session['role']=user['role']
    csrf_token()

def configure_security(app):
    @app.context_processor
    def context():
        return {'user':getattr(g,'user',None),'csrf_token':csrf_token}

    @app.before_request
    def guard():
        if request.endpoint=='static':return
        g.user=AuthService.current(session.get('user_id'))
        api=request.path.startswith('/api/')
        public=request.path in ('/','/login','/register','/api/v1/auth/csrf','/api/v1/auth/register','/api/v1/auth/login')
        if not public and not g.user:
            session.pop('user_id',None)
            if api:raise DomainError('請使用已核准帳號登入','UNAUTHORIZED',401)
            return redirect('/login')
        exempt_password=request.path in ('/password','/logout','/api/v1/auth/password','/api/v1/auth/logout','/api/v1/auth/csrf')
        if g.user and g.user['must_change_password'] and not public and not exempt_password:
            if api:raise DomainError('請先修改預設密碼','PASSWORD_CHANGE_REQUIRED',403)
            return redirect('/password')
        if request.path.startswith(('/admin','/api/v1/admin')) and g.user and g.user['role']!='admin':
            raise DomainError('需要管理者權限','FORBIDDEN',403)
        if request.method in ('POST','PATCH','DELETE','PUT'):
            expected=session.get('csrf_token','')
            supplied=request.headers.get('X-CSRF-Token') or request.form.get('csrf_token','')
            if not expected or not secrets.compare_digest(expected,supplied):
                raise DomainError('驗證碼已失效，請重新整理頁面','CSRF',403)

    @app.errorhandler(DomainError)
    def domain_error(exc):
        if request.path.startswith('/api/'):
            return jsonify(error={'code':exc.code,'message':str(exc),'details':None}),exc.status
        return str(exc),exc.status
