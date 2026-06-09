from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class UserRole(str, enum.Enum):
    USER = "user"
    STAFF = "staff"
    ADMIN = "admin"


class User(BaseModel):
    __tablename__ = "users"

    phone = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50))
    avatar = Column(String(255))
    role = Column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]), default=UserRole.USER, nullable=False)

    bookings = relationship("Booking", back_populates="user")
    members = relationship("Member", back_populates="user")
    cat_infos = relationship("CatInfo", back_populates="user")
    employee = relationship("Employee", back_populates="user", uselist=False)
