from ..repositories.monitoring_repository import MonitoringRepository
from .member_service import MemberService
from .resource_service import ResourceService
from .errors import DomainError

class MonitoringService:
    @staticmethod
    def snapshot():
        result=MonitoringRepository.snapshot()
        result['laboratories']=ResourceService.list('laboratories')
        result['cameras']=ResourceService.list('cameras')
        return result
    @staticmethod
    def resolve(actor,aid,status):
        MemberService.require_admin(actor)
        if status!='resolved':raise DomainError('警示狀態僅可更新為 resolved')
        alert=MonitoringRepository.alert(aid)
        if not alert:raise DomainError('找不到警示','NOT_FOUND',404)
        if alert['status']!='open':raise DomainError('警示已處理','CONFLICT',409)
        MonitoringRepository.resolve_alert(aid,actor)
        return {'message':'警示已處理'}
