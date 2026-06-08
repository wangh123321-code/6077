from sqlalchemy import Column, String, Integer, Numeric, Date, ForeignKey, Enum, Index, text
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Booking(BaseModel):
    __tablename__ = "bookings"
    __table_args__ = (
        Index(
            "unique_room_date_booking",
            "cat_room_id", "check_in_date", "check_out_date",
            unique=True,
            postgresql_where=text("status NOT IN ('cancelled', 'refunded')")
        ),
    )

    order_no = Column(String(32), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    cat_room_id = Column(Integer, ForeignKey("cat_rooms.id"), nullable=False, index=True)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    cat_name = Column(String(50))
    cat_age = Column(Integer)
    cat_food_brand = Column(String(100))
    special_requirements = Column(String(500))
    status = Column(Enum(BookingStatus, values_callable=lambda x: [e.value for e in x]), default=BookingStatus.PENDING, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    verify_code = Column(String(32), unique=True, index=True)

    user = relationship("User", back_populates="bookings")
    cat_room = relationship("CatRoom", back_populates="bookings")
    booking_services = relationship("BookingService", back_populates="booking")
    payments = relationship("Payment", back_populates="booking")
    refunds = relationship("Refund", back_populates="booking")
