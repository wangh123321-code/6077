from typing import Optional, Annotated
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from app.models.service import ServiceType


class ServiceBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    name: str = Field(..., description="服务名称", max_length=100)
    description: Optional[str] = Field(None, description="描述", max_length=500)
    price: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(..., description="价格", gt=0)
    type: ServiceType = Field(default=ServiceType.BASIC, description="服务类型")
    duration: Optional[int] = Field(None, description="服务时长（分钟）", ge=0)
    applicable_scene: Optional[str] = Field(None, description="适用场景", max_length=200)


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, description="服务名称", max_length=100)
    description: Optional[str] = Field(None, description="描述", max_length=500)
    price: Optional[Annotated[Decimal, Field(max_digits=10, decimal_places=2)]] = Field(None, description="价格", gt=0)
    type: Optional[ServiceType] = Field(None, description="服务类型")
    duration: Optional[int] = Field(None, description="服务时长（分钟）", ge=0)
    applicable_scene: Optional[str] = Field(None, description="适用场景", max_length=200)


class ServiceResponse(ServiceBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ServiceQuery(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: Optional[ServiceType] = Field(None, description="按类型筛选")
