from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel


class Member(BaseModel):
    __tablename__ = "members"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    level = Column(Integer, default=1, nullable=False)
    points = Column(Integer, default=0)
    balance = Column(Numeric(10, 2), default=0)
    valid_until = Column(Date)

    user = relationship("User", back_populates="members")
