from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class CatInfoCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="猫咪名字")
    breed: Optional[str] = Field(None, description="品种")
    age: Optional[int] = Field(None, description="年龄")
    gender: Optional[str] = Field(None, description="性别")
    weight: Optional[Decimal] = Field(None, description="体重")
    vaccine_status: List[str] = Field(default_factory=list, description="疫苗状态")
    health_record: Optional[str] = Field(None, description="健康记录")


class CatInfoUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, description="猫咪名字")
    breed: Optional[str] = Field(None, description="品种")
    age: Optional[int] = Field(None, description="年龄")
    gender: Optional[str] = Field(None, description="性别")
    weight: Optional[Decimal] = Field(None, description="体重")
    vaccine_status: Optional[List[str]] = Field(None, description="疫苗状态")
    health_record: Optional[str] = Field(None, description="健康记录")


class CatInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    breed: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    weight: Optional[Decimal]
    vaccine_status: List[str]
    health_record: Optional[str]
    created_at: datetime
    updated_at: datetime
