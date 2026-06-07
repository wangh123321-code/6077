from sqlalchemy import Column, String, Numeric, Enum, Integer
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class ServiceType(str, enum.Enum):
    BASIC = "basic"
    ADDON = "addon"


class Service(BaseModel):
    __tablename__ = "services"

    name = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Numeric(10, 2), nullable=False)
    type = Column(Enum(ServiceType), default=ServiceType.BASIC, nullable=False)
    duration = Column(Integer)
    applicable_scene = Column(String(200))

    booking_services = relationship("BookingService", back_populates="service")
