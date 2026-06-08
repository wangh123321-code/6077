from sqlalchemy import Column, String, Numeric, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class PaymentMethod(str, enum.Enum):
    WECHAT = "wechat"
    ALIPAY = "alipay"
    CARD = "card"
    BALANCE = "balance"
    CASH = "cash"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(BaseModel):
    __tablename__ = "payments"

    order_no = Column(String(32), ForeignKey("bookings.order_no"), nullable=False, index=True)
    payment_method = Column(Enum(PaymentMethod, values_callable=lambda x: [e.value for e in x]), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    transaction_id = Column(String(100), unique=True, index=True)
    status = Column(Enum(PaymentStatus, values_callable=lambda x: [e.value for e in x]), default=PaymentStatus.PENDING, nullable=False)
    callback_data = Column(Text)

    booking = relationship("Booking", back_populates="payments")
