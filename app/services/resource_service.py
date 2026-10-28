import sqlite3
from .errors import DomainError,required_text
from .member_service import MemberService
from ..repositories.resource_repository import ResourceRepository

class ResourceService:
    @staticmethod
    def list(kind,actor=None):
        if actor is not None:MemberService.require_admin(actor)
        return [dict(row) for row in ResourceRepository.list(kind,active_only=actor is None)]
    @staticmethod
    def save(actor,kind,data,rid=None):
        MemberService.require_admin(actor)
        if not isinstance(data,dict):raise DomainError('請提供 JSON 物件')
        existing=ResourceRepository.by_id(kind,rid) if rid is not None else None
        if rid is not None and not existing:raise DomainError('找不到資源','NOT_FOUND',404)
        values=dict(existing) if existing else {'active':1,'device_index':0}
        values.update(data)
        values['name']=required_text(values.get('name'),'名稱',100)
        if type(values.get('active')) not in (int,bool) or values['active'] not in (0,1):raise DomainError('啟用狀態須為 0 或 1')
        if kind=='laboratories':values['location']=required_text(values.get('location'),'位置',200)
        else:
            if type(values.get('laboratory_id')) is not int or values['laboratory_id']<=0:raise DomainError('請選擇有效實驗室')
            lab=ResourceRepository.by_id('laboratories',values['laboratory_id'])
            if not lab:raise DomainError('找不到實驗室','NOT_FOUND',404)
            if values['active'] and not lab['active']:raise DomainError('不可啟用停用實驗室的攝影機','CONFLICT',409)
            if type(values.get('device_index')) is not int or values['device_index']<0:raise DomainError('設備索引須為非負整數')
        try:return ResourceRepository.save(kind,values,rid)
        except sqlite3.IntegrityError:raise DomainError('資源名稱重複或關聯無效','CONFLICT',409) from None
