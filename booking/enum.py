from enum import Enum

class BookingStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    OCCUPIED = "occupied"
    COMPLETED = "completed"

class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

class BookingType(Enum):
    HOURLY = "hourly"
    EVENT = "event"
    
class PlayerStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class PlayerType(Enum):
    JOINED = "joined"
    INVITED = "invited"