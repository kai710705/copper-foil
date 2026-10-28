from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..services.auth_service import AuthService
from ..services.booking_service import BookingService
from ..repositories.user_repository import UserRepository
from ..repositories.booking_repository import BookingRepository
from ..repositories.database import get_db
from ..services.errors import DomainError
from .security import establish_login
from flask import g
mvc_bp=Blueprint('mvc',__name__)
def login_required(): return session.get('user_id')
@mvc_bp.route('/')
def home(): return render_template('calendar.html')
@mvc_bp.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=AuthService.login(request.form.get('username'),request.form.get('password'))
        if u:
            establish_login(u)
            return redirect('/password' if u['must_change_password'] else '/')
        flash('帳號或密碼錯誤','error')
    return render_template('auth.html',mode='login')
@mvc_bp.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        try: AuthService.register(request.form.get('username'),request.form.get('email'),request.form.get('password'),request.form.get('role','user')); flash('註冊成功，請等待管理者審核','success'); return redirect(url_for('mvc.login'))
        except DomainError as exc:
            flash(str(exc),'error')
            return render_template('auth.html',mode='register'), exc.status
    return render_template('auth.html',mode='register')
@mvc_bp.route('/logout',methods=['POST'])
def logout(): session.clear(); return redirect(url_for('mvc.home'))
@mvc_bp.route('/password',methods=['GET','POST'])
def password():
    if request.method=='POST':
        try:
            AuthService.change_password(g.user['id'],request.form.get('current_password'),request.form.get('password'))
            return redirect('/admin' if g.user['role']=='admin' else '/')
        except DomainError as exc:
            flash(str(exc),'error')
            return render_template('password.html'),exc.status
    return render_template('password.html')
@mvc_bp.route('/admin')
def admin():
    return render_template('admin.html')
