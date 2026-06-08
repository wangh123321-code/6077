from sqlalchemy import Column, String, Numeric, Integer, Enum, ARRAY
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class CatRoomStatus(str, enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    CLEANING = "cleaning"


class CatRoom(BaseModel):
    __tablename__ = "cat_rooms"

    name = Column(String(100), nullable=False)
    description = Column(String(500))
    price_per_day = Column(Numeric(10, 2), nullable=False)
    facilities = Column(ARRAY(String), default=[])
    images = Column(ARRAY(String), default=[])
    status = Column(Enum(CatRoomStatus, values_callable=lambda x: [e.value for e in x]), default=CatRoomStatus.AVAILABLE, nullable=False)
    area = Column(Numeric(5, 2))
    floor = Column(Integer)
    location = Column(String(200))

    bookings = relationship("Booking", back_populates="cat_room")
