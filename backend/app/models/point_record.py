from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class PointType(str, enum.Enum):
    EARN = "earn"
    SPEND = "spend"
    EXCHANGE = "exchange"
    EXPIRED = "expired"


class PointRecord(BaseModel):
    __tablename__ = "point_records"

    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    type = Column(Enum(PointType), nullable=False)
    points = Column(Integer, nullable=False)
    description = Column(String(200), nullable=False)
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    related_order_no = Column(String(32), index=True)
