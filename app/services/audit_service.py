from datetime import date
from .member_service import MemberService
from .errors import DomainError,required_text
from ..repositories.audit_repository import AuditRepository
from ..repositories.resource_repository import ResourceRepository

class AuditService:
    @staticmethod
    def create(actor,data):
        MemberService.require_admin(actor)
        if not isinstance(data,dict):raise DomainError('請提供 JSON 物件')
        values={key:required_text(data.get(key),label,maximum) for key,label,maximum in [('area','區域',200),('inspector','稽核人員',100),('issue','問題',2000),('due_date','改善期限',10)]}
        try:
            if date.fromisoformat(values['due_date']).isoformat()!=values['due_date']:raise ValueError()
        except ValueError:raise DomainError('改善期限須為有效 YYYY-MM-DD 日期') from None
        lid=data.get('laboratory_id')
        if lid is not None:
            if type(lid) is not int or not ResourceRepository.by_id('laboratories',lid):raise DomainError('找不到實驗室','NOT_FOUND',404)
        values['laboratory_id']=lid
        return AuditRepository.create(values,actor)
    @staticmethod
    def complete(actor,aid,status):
        MemberService.require_admin(actor)
        if status!='completed':raise DomainError('稽核狀態僅可更新為 completed')
        audit=AuditRepository.by_id(aid)
        if not audit:raise DomainError('找不到稽核紀錄','NOT_FOUND',404)
        if audit['status']!='open':raise DomainError('稽核已完成','CONFLICT',409)
        return AuditRepository.complete(aid)
