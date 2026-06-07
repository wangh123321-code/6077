from sqlalchemy import Column, String, Numeric, Text, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class Refund(BaseModel):
    __tablename__ = "refunds"

    order_no = Column(String(32), ForeignKey("bookings.order_no"), nullable=False, index=True)
    refund_amount = Column(Numeric(10, 2), nullable=False)
    refund_reason = Column(String(500))
    status = Column(Enum(RefundStatus), default=RefundStatus.PENDING, nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), index=True)

    booking = relationship("Booking", back_populates="refunds")
