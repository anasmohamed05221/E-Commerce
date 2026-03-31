from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class InventoryChangeReason(str, Enum):
    SALE = "sale"
    RESTOCK = "restock"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    CANCELLATION = "cancellation"

class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"