from ..repositories.booking_repository import BookingRepository
class BookingService:
    @staticmethod
    def create(uid,data):
        kind=data.get('booking_type','personal'); status='pending' if kind=='room' else 'confirmed'
        BookingRepository.create(uid,data['title'],data['start_at'],data['end_at'],kind,data.get('room_id'),data.get('notes',''),status)
