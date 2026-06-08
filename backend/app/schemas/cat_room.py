from typing import Optional, List, Annotated
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from app.models.cat_room import CatRoomStatus


class CatRoomBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    name: str = Field(..., description="猫屋名称", max_length=100)
    description: Optional[str] = Field(None, description="描述", max_length=500)
    price_per_day: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(..., description="日价格", gt=0)
    facilities: Optional[List[str]] = Field(default_factory=list, description="设施列表")
    images: Optional[List[str]] = Field(default_factory=list, description="图片URL列表")
    status: CatRoomStatus = Field(default=CatRoomStatus.AVAILABLE, description="状态")
    area: Optional[Annotated[Decimal, Field(max_digits=5, decimal_places=2)]] = Field(None, description="面积")
    floor: Optional[int] = Field(None, description="楼层")
    location: Optional[str] = Field(None, description="位置", max_length=200)


class CatRoomCreate(CatRoomBase):
    pass


class CatRoomUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, description="猫屋名称", max_length=100)
    description: Optional[str] = Field(None, description="描述", max_length=500)
    price_per_day: Optional[Annotated[Decimal, Field(max_digits=10, decimal_places=2)]] = Field(None, description="日价格", gt=0)
    facilities: Optional[List[str]] = Field(None, description="设施列表")
    images: Optional[List[str]] = Field(None, description="图片URL列表")
    status: Optional[CatRoomStatus] = Field(None, description="状态")
    area: Optional[Annotated[Decimal, Field(max_digits=5, decimal_places=2)]] = Field(None, description="面积")
    floor: Optional[int] = Field(None, description="楼层")
    location: Optional[str] = Field(None, description="位置", max_length=200)


class CatRoomResponse(CatRoomBase):
    id: int
    created_at: datetime
    updated_at: datetime


class CatRoomListItem(CatRoomResponse):
    pass


class CatRoomListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[CatRoomListItem]
    total: int
    page: int
    page_size: int


class CatRoomQuery(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    status: Optional[CatRoomStatus] = Field(None, description="按状态筛选")
    min_price: Optional[Decimal] = Field(None, description="最低价格", ge=0)
    max_price: Optional[Decimal] = Field(None, description="最高价格", ge=0)


class CatRoomAvailabilityQuery(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    check_in_date: date = Field(..., description="入住日期")
    check_out_date: date = Field(..., description="退房日期")


AvailabilityQueryRequest = CatRoomAvailabilityQuery
