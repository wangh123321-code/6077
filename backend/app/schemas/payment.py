from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from app.models.payment import PaymentMethod, PaymentStatus


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    payment_method: PaymentMethod
    amount: Decimal
    transaction_id: Optional[str] = None
    status: PaymentStatus
    callback_data: Optional[str] = None
    payment_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaymentCallbackRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_no: str = Field(..., description="订单号")
    transaction_id: str = Field(..., description="第三方交易号")
    amount: Decimal = Field(..., description="支付金额")
    status: str = Field(..., description="支付状态")
    payment_method: str = Field(..., description="支付方式")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="原始回调数据")


class PaymentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_no: str = Field(..., description="订单号")
    payment_method: PaymentMethod = Field(..., description="支付方式")
    amount: Decimal = Field(..., description="支付金额", gt=0)


PaymentCallback = PaymentCallbackRequest
