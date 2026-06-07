from typing import Any, List, Optional
from datetime import date
from decimal import Decimal
import math

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func, and_, or_, not_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.core.errors import NotFoundException, ParameterValidationException, ErrorCode
from app.models.booking import Booking, BookingStatus
from app.models.cat_room import CatRoom, CatRoomStatus
from app.models.user import User
from app.schemas import (
    ApiResponse,
    CatRoomCreate,
    CatRoomResponse,
    CatRoomUpdate,
    PaginationResponse,
)

router = APIRouter()


@router.get("", response_model=ApiResponse[PaginationResponse[CatRoomResponse]])
async def get_cat_rooms(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[CatRoomStatus] = Query(None, description="按状态筛选"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="最低价格"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="最高价格"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    query = select(CatRoom)

    if status:
        query = query.where(CatRoom.status == status)

    if min_price is not None:
        query = query.where(CatRoom.price_per_day >= min_price)

    if max_price is not None:
        query = query.where(CatRoom.price_per_day <= max_price)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(CatRoom.id.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return ApiResponse(
        code=0,
        message="success",
        data=PaginationResponse(
            items=[CatRoomResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get("/availability", response_model=ApiResponse[List[CatRoomResponse]])
async def get_available_cat_rooms(
    check_in_date: date = Query(..., description="入住日期"),
    check_out_date: date = Query(..., description="退房日期"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    if check_in_date >= check_out_date:
        raise ParameterValidationException(message="入住日期必须早于退房日期")

    if check_in_date < date.today():
        raise ParameterValidationException(message="入住日期不能早于今天")

    booked_rooms_subquery = (
        select(Booking.cat_room_id)
        .where(
            and_(
                Booking.status.notin_([BookingStatus.CANCELLED, BookingStatus.REFUNDED]),
                or_(
                    and_(
                        Booking.check_in_date < check_out_date,
                        Booking.check_out_date > check_in_date,
                    ),
                ),
            )
        )
        .subquery()
    )

    query = select(CatRoom).where(
        and_(
            CatRoom.status == CatRoomStatus.AVAILABLE,
            CatRoom.id.notin_(select(booked_rooms_subquery)),
        )
    )

    result = await db.execute(query)
    items = result.scalars().all()

    return ApiResponse(
        code=0,
        message="success",
        data=[CatRoomResponse.model_validate(item) for item in items],
    )


@router.get("/{room_id}", response_model=ApiResponse[CatRoomResponse])
async def get_cat_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(CatRoom).where(CatRoom.id == room_id))
    cat_room = result.scalar_one_or_none()

    if not cat_room:
        raise NotFoundException(
            message="猫屋不存在",
            code=ErrorCode.RECORD_NOT_FOUND,
        )

    return ApiResponse(
        code=0,
        message="success",
        data=CatRoomResponse.model_validate(cat_room),
    )


@router.post("", response_model=ApiResponse[CatRoomResponse], status_code=status.HTTP_201_CREATED)
async def create_cat_room(
    room_data: CatRoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> Any:
    new_room = CatRoom(
        name=room_data.name,
        description=room_data.description,
        price_per_day=room_data.price_per_day,
        facilities=room_data.facilities,
        images=room_data.images,
        status=room_data.status,
        area=room_data.area,
        floor=room_data.floor,
        location=room_data.location,
    )

    db.add(new_room)
    await db.commit()
    await db.refresh(new_room)

    return ApiResponse(
        code=0,
        message="创建成功",
        data=CatRoomResponse.model_validate(new_room),
    )


@router.put("/{room_id}", response_model=ApiResponse[CatRoomResponse])
async def update_cat_room(
    room_id: int,
    room_data: CatRoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> Any:
    result = await db.execute(select(CatRoom).where(CatRoom.id == room_id))
    cat_room = result.scalar_one_or_none()

    if not cat_room:
        raise NotFoundException(
            message="猫屋不存在",
            code=ErrorCode.RECORD_NOT_FOUND,
        )

    update_data = room_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cat_room, field, value)

    await db.commit()
    await db.refresh(cat_room)

    return ApiResponse(
        code=0,
        message="更新成功",
        data=CatRoomResponse.model_validate(cat_room),
    )


@router.delete("/{room_id}", response_model=ApiResponse[dict])
async def delete_cat_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> Any:
    result = await db.execute(select(CatRoom).where(CatRoom.id == room_id))
    cat_room = result.scalar_one_or_none()

    if not cat_room:
        raise NotFoundException(
            message="猫屋不存在",
            code=ErrorCode.RECORD_NOT_FOUND,
        )

    await db.delete(cat_room)
    await db.commit()

    return ApiResponse(
        code=0,
        message="删除成功",
        data={},
    )
