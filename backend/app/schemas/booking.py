from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from app.models.booking import BookingStatus
from app.models.booking_service import BookingServiceStatus
from app.schemas.cat_room import CatRoomResponse
from app.schemas.service import ServiceResponse


class AddonServiceRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    service_id: int = Field(..., description="服务ID")
    quantity: int = Field(1, ge=1, description="数量")


class BookingCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cat_room_id: int = Field(..., description="猫屋ID")
    check_in_date: date = Field(..., description="入住日期")
    check_out_date: date = Field(..., description="退房日期")
    cat_name: Optional[str] = Field(None, description="猫咪名字")
    cat_age: Optional[int] = Field(None, description="猫咪年龄")
    cat_food_brand: Optional[str] = Field(None, description="猫粮品牌")
    special_requirements: Optional[str] = Field(None, description="特殊要求")
    addon_services: List[AddonServiceRequest] = Field(default_factory=list, description="加购服务列表")


class BookingServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_id: int
    service_id: int
    service: Optional[ServiceResponse] = None
    quantity: int
    price: Decimal
    execute_time: Optional[datetime]
    executor_id: Optional[int]
    status: BookingServiceStatus
    created_at: datetime
    updated_at: datetime


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    user_id: int
    cat_room_id: int
    cat_room: Optional[CatRoomResponse] = None
    check_in_date: date
    check_out_date: date
    cat_name: Optional[str]
    cat_age: Optional[int]
    cat_food_brand: Optional[str]
    special_requirements: Optional[str]
    status: BookingStatus
    total_price: Decimal
    verify_code: Optional[str]
    booking_services: List[BookingServiceResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class BookingStatusUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: BookingStatus = Field(..., description="预订状态")


class BookingAvailabilityQueryRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    check_in_date: date = Field(..., description="入住日期")
    check_out_date: date = Field(..., description="退房日期")
    cat_room_id: Optional[int] = Field(None, description="猫屋ID（可选）")


class AvailableCatRoomItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cat_room: CatRoomResponse
    price: Decimal
    available: bool = True


class BookingAvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    check_in_date: date
    check_out_date: date
    available_rooms: List[AvailableCatRoomItem]
    total_days: int


class BookingAddonServiceRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    booking_id: int = Field(..., description="预订ID")
    addon_services: List[AddonServiceRequest] = Field(..., description="加购服务列表")


class PaymentRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_no: str = Field(..., description="订单号")
    payment_method: str = Field(..., description="支付方式")


class RefundRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_no: str = Field(..., description="订单号")
    refund_reason: Optional[str] = Field(None, description="退款原因")


class VerifyRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    verify_code: str = Field(..., description="核销码")
