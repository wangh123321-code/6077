from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class BookingServiceStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BookingService(BaseModel):
    __tablename__ = "booking_services"

    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    execute_time = Column(DateTime)
    executor_id = Column(Integer, ForeignKey("users.id"), index=True)
    status = Column(Enum(BookingServiceStatus, values_callable=lambda x: [e.value for e in x]), default=BookingServiceStatus.PENDING, nullable=False)

    booking = relationship("Booking", back_populates="booking_services")
    service = relationship("Service", back_populates="booking_services")
