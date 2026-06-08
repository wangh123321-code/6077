from datetime import datetime, date
from typing import Optional, List, Annotated
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

from .common import PaginationRequest


class PointType(str, Enum):
    EARN = "earn"
    SPEND = "spend"
    EXCHANGE = "exchange"
    EXPIRED = "expired"


class MemberRechargeRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(..., gt=0, description="充值金额")
    payment_method: str = Field("wechat", description="支付方式")


class PointExchangeRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    points: int = Field(..., gt=0, description="兑换积分数量")
    exchange_item: str = Field(..., description="兑换物品")


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    level: int
    points: int
    balance: Decimal
    valid_until: Optional[date] = None
    created_at: datetime
    updated_at: datetime


class PointRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    type: PointType
    points: int
    description: str
    balance_before: int
    balance_after: int
    related_order_no: Optional[str] = None
    created_at: datetime


class PointRecordFilterRequest(PaginationRequest):
    model_config = ConfigDict(from_attributes=True)

    type: Optional[PointType] = Field(None, description="积分类型")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")


class RechargeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    member_id: int
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    payment_url: Optional[str] = None
    transaction_id: Optional[str] = None
    status: str
    created_at: datetime


class PointExchangeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    member_id: int
    points: int
    exchange_item: str
    points_before: int
    points_after: int
    status: str
    created_at: datetime


MemberRecharge = MemberRechargeRequest

PointsRecord = PointRecordResponse
