from ..repositories.user_repository import UserRepository

class CameraAuthService:
    @staticmethod
    def approved(uid):
        user = UserRepository.by_id(uid) if uid else None
        return bool(user and user['approval_status'] == 'approved')
