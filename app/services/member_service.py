from .auth_service import AuthService
from .errors import DomainError
from ..repositories.user_repository import UserRepository

class MemberService:
    @staticmethod
    def require_admin(actor):
        user=AuthService.current(actor)
        if not user or user['role']!='admin':raise DomainError('需要管理者權限','FORBIDDEN',403)
        if user['must_change_password']:raise DomainError('請先修改預設密碼','PASSWORD_CHANGE_REQUIRED',403)
    @classmethod
    def review(cls,actor,uid,status):
        if status not in ('approved','rejected','disabled'):raise DomainError('會員狀態不正確')
        with UserRepository.transaction():
            cls.require_admin(actor)
            member=UserRepository.by_id(uid)
            if not member:raise DomainError('找不到會員','NOT_FOUND',404)
            allowed={'pending':('approved','rejected'),'approved':('disabled',)}
            if status not in allowed.get(member['approval_status'],()):raise DomainError('不允許此狀態變更','CONFLICT',409)
            if status=='disabled' and (actor==uid or (member['role']=='admin' and UserRepository.approved_admin_count()<=1)):
                raise DomainError('不可停用自己或最後一位管理者','CONFLICT',409)
            UserRepository.review(uid,actor,member['approval_status'],status)
        return {'message':'會員狀態已更新'}
    @classmethod
    def list(cls,actor,status=None):
        cls.require_admin(actor)
        if status and status not in ('pending','approved','rejected','disabled'):raise DomainError('篩選狀態不正確')
        return [dict(r) for r in UserRepository.all(status)]
    @classmethod
    def history(cls,actor,uid):
        cls.require_admin(actor)
        if not UserRepository.by_id(uid):raise DomainError('找不到會員','NOT_FOUND',404)
        return [dict(r) for r in UserRepository.history(uid)]
