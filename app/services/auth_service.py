from werkzeug.security import check_password_hash, generate_password_hash
from ..repositories.user_repository import UserRepository
from .errors import DomainError, required_text
import re
import sqlite3
class AuthService:
    @staticmethod
    def login(username,password):
        if not isinstance(username,str) or not isinstance(password,str):return None
        u=UserRepository.by_username(username)
        return u if u and u['approval_status']=='approved' and check_password_hash(u['password_hash'],password) else None
    @staticmethod
    def current(uid):
        user=UserRepository.by_id(uid) if uid else None
        return dict(user) if user and user['approval_status']=='approved' else None
    @staticmethod
    def change_password(uid,current_password,password):
        user=UserRepository.credentials(uid)
        if not user or user['approval_status']!='approved':raise DomainError('請先登入','UNAUTHORIZED',401)
        if not isinstance(current_password,str) or not check_password_hash(user['password_hash'],current_password):
            raise DomainError('目前密碼不正確')
        if not isinstance(password,str) or not 8<=len(password)<=128 or password=='admin@123' or password==current_password:
            raise DomainError('新密碼須為 8 至 128 字元，且不可與目前或預設密碼相同')
        UserRepository.change_password(uid,generate_password_hash(password))
    @staticmethod
    def register(username,email,password,role='user'):
        username=required_text(username,'帳號',50)
        email=required_text(email,'Email',254).lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):
            raise DomainError('Email 格式不正確')
        if not isinstance(password,str) or not 8 <= len(password) <= 128:
            raise DomainError('密碼長度須為 8 至 128 字元')
        if role not in ('user','admin'):
            raise DomainError('角色僅允許一般使用者或管理者')
        try:
            UserRepository.create(username,email,generate_password_hash(password),role)
        except sqlite3.IntegrityError:
            raise DomainError('帳號或 Email 已存在','CONFLICT',409) from None
