from sqlalchemy import Column, String, Integer, Numeric, Text, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from .base import BaseModel


class CatInfo(BaseModel):
    __tablename__ = "cat_infos"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    breed = Column(String(50))
    age = Column(Integer)
    gender = Column(String(10))
    weight = Column(Numeric(5, 2))
    vaccine_status = Column(ARRAY(String), default=[])
    health_record = Column(Text)

    user = relationship("User", back_populates="cat_infos")
