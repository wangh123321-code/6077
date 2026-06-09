"""
数据模型模块
所有SQLAlchemy ORM模型定义在此
"""
from app.models.base import Base, BaseModel
from app.models.user import User, UserRole
from app.models.cat_room import CatRoom, CatRoomStatus
from app.models.service import Service, ServiceType
from app.models.booking import Booking, BookingStatus
from app.models.booking_service import BookingService, BookingServiceStatus
from app.models.cat_info import CatInfo
from app.models.member import Member
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.refund import Refund, RefundStatus
from app.models.schedule import (
    Employee,
    Shift,
    SchedulingRule,
    Schedule,
    LeaveRequest,
    ShiftSwap,
    ShiftPreference,
    Attendance,
    AttendanceAlert,
    SkillTag,
    ShiftType,
    LeaveType,
    RequestStatus,
    AttendanceStatus,
    AlertType,
)

__all__ = [
    "Base",
    "BaseModel",
    "User",
    "UserRole",
    "CatRoom",
    "CatRoomStatus",
    "Service",
    "ServiceType",
    "Booking",
    "BookingStatus",
    "BookingService",
    "BookingServiceStatus",
    "CatInfo",
    "Member",
    "Payment",
    "PaymentStatus",
    "PaymentMethod",
    "Refund",
    "RefundStatus",
    "Employee",
    "Shift",
    "SchedulingRule",
    "Schedule",
    "LeaveRequest",
    "ShiftSwap",
    "ShiftPreference",
    "Attendance",
    "AttendanceAlert",
    "SkillTag",
    "ShiftType",
    "LeaveType",
    "RequestStatus",
    "AttendanceStatus",
    "AlertType",
]
