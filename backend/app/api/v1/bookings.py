import logging
import uuid
import random
import io
import base64
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

import qrcode

from app.api.deps import get_db, get_current_user, get_current_staff, get_current_active_user
from app.core.errors import (
    BusinessException,
    ErrorCode,
    NotFoundException,
    ConflictException,
    ParameterValidationException,
    ForbiddenException
)
from app.utils.redis_lock import redis_lock
from app.utils.payment import payment_service
from app.models.booking import Booking, BookingStatus
from app.models.booking_service import BookingService, BookingServiceStatus
from app.models.cat_room import CatRoom, CatRoomStatus
from app.models.service import Service
from app.models.payment import PaymentMethod
from app.models.refund import Refund, RefundStatus
from app.models.user import User
from app.schemas import (
    ApiResponse,
    PaginationResponse,
    BookingCreateRequest,
    BookingResponse as SchemaBookingResponse,
    BookingServiceResponse as SchemaBookingServiceResponse,
    VerifyRequest,
    RefundRequest,
    AddonServiceRequest,
    PaginationRequest,
)
from app.schemas.booking import (
    BookingFilterRequest,
    RefundAmountResponse,
    BookingQRCodeResponse,
    AddServiceRequest,
    CancelBookingRequest,
    BookingServiceResponse,
    BookingResponse
)
from app.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def get_user_id(user: User) -> int:
    return user.id


def generate_order_no() -> str:
    """生成唯一订单号：CH{yyyyMMdd}{8位随机}"""
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = "".join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=8))
    return f"CH{date_str}{random_str}"


def generate_verify_code() -> str:
    """生成唯一核销码"""
    return uuid.uuid4().hex[:16].upper()


def calculate_days(check_in: date, check_out: date) -> int:
    """计算入住天数"""
    return (check_out - check_in).days


def generate_qr_code_base64(data: str) -> str:
    """生成二维码并返回Base64编码"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


async def get_cat_room_price(db: AsyncSession, cat_room_id: int) -> Decimal:
    """获取猫屋价格"""
    result = await db.execute(
        select(CatRoom.price_per_day).where(CatRoom.id == cat_room_id)
    )
    price = result.scalar_one_or_none()
    if price is None:
        raise NotFoundException(f"猫屋 {cat_room_id} 不存在", ErrorCode.NOT_FOUND)
    return price


async def get_service_price(db: AsyncSession, service_id: int) -> Decimal:
    """获取服务价格"""
    result = await db.execute(
        select(Service.price).where(Service.id == service_id)
    )
    price = result.scalar_one_or_none()
    if price is None:
        raise NotFoundException(f"服务 {service_id} 不存在", ErrorCode.NOT_FOUND)
    return price


async def check_room_availability(
    db: AsyncSession,
    cat_room_id: int,
    check_in_date: date,
    check_out_date: date,
    exclude_booking_id: Optional[int] = None
) -> bool:
    """
    检查猫屋在指定时间段是否可用

    时间段重叠判断：
    已有预订的入住 < 新预订的退房 AND 已有预订的退房 > 新预订的入住
    """
    query = select(func.count(Booking.id)).where(
        and_(
            Booking.cat_room_id == cat_room_id,
            Booking.status.notin_([BookingStatus.CANCELLED, BookingStatus.REFUNDED]),
            Booking.check_in_date < check_out_date,
            Booking.check_out_date > check_in_date
        )
    )

    if exclude_booking_id is not None:
        query = query.where(Booking.id != exclude_booking_id)

    result = await db.execute(query)
    count = result.scalar_one()
    return count == 0


async def calculate_total_price(
    db: AsyncSession,
    cat_room_id: int,
    check_in_date: date,
    check_out_date: date,
    services: List[Tuple[int, int]]
) -> Decimal:
    """
    计算总价
    总价 = 猫屋价格*天数 + 加购服务价格*数量
    """
    days = calculate_days(check_in_date, check_out_date)
    if days <= 0:
        raise ParameterValidationException("退房日期必须晚于入住日期")

    room_price = await get_cat_room_price(db, cat_room_id)
    total = room_price * days

    for service_id, quantity in services:
        service_price = await get_service_price(db, service_id)
        total += service_price * quantity

    return total


def calculate_refund_amount(
    booking: Booking,
    cancel_time: datetime
) -> Tuple[Decimal, Decimal, str, bool, Optional[str]]:
    """
    计算退款金额

    退款规则（可配置）：
    - 提前 >= REFUND_DAYS_FULL 天取消：全额退款
    - 提前 REFUND_DAYS_PARTIAL 到 REFUND_DAYS_FULL 天取消：退还 REFUND_PARTIAL_RATE * 100%
    - 提前 < REFUND_NO_REFUND_DAYS 天取消：不退款
    - 已入住或已退房：不允许退款

    Returns:
        (退款金额, 手续费, 规则说明, 是否可退款, 原因)
    """
    original_amount = booking.total_price

    if booking.status in [BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT]:
        return Decimal(0), Decimal(0), "已入住/已退房不允许退款", False, "订单已使用，无法退款"

    if booking.status in [BookingStatus.CANCELLED, BookingStatus.REFUNDED]:
        return Decimal(0), Decimal(0), "订单已取消/已退款", False, "订单状态不允许退款"

    check_in_datetime = datetime.combine(booking.check_in_date, datetime.min.time())
    days_before_checkin = (check_in_datetime - cancel_time).total_seconds() / (24 * 3600)

    if days_before_checkin >= settings.REFUND_DAYS_FULL:
        refund_rate = Decimal("1.0")
        rule = f"提前{settings.REFUND_DAYS_FULL}天以上取消，全额退款"
    elif days_before_checkin >= settings.REFUND_DAYS_PARTIAL:
        refund_rate = Decimal(str(settings.REFUND_PARTIAL_RATE))
        rule = (
            f"提前{settings.REFUND_DAYS_PARTIAL}-{settings.REFUND_DAYS_FULL}天取消，"
            f"退还{int(refund_rate * 100)}%"
        )
    else:
        return Decimal(0), Decimal(0), f"提前不足{settings.REFUND_NO_REFUND_DAYS}天不允许退款", False, "距离入住时间太近，无法退款"

    refund_amount = original_amount * refund_rate
    fee = Decimal(0)

    return refund_amount, fee, rule, True, None


@router.post("", response_model=ApiResponse[BookingResponse], summary="创建预订")
async def create_booking(
    request: BookingCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建预订（核心接口，双重锁并发控制）

    并发控制策略：
    1. Redis分布式锁：防止同一猫屋同一时间段的并发预订
    2. 数据库乐观锁：使用version字段防止更新冲突
    3. 数据库唯一约束：(cat_room_id, check_in_date, check_out_date, status) 作为最后防线
    """
    user_id = get_user_id(current_user)

    if request.check_in_date >= request.check_out_date:
        raise ParameterValidationException("退房日期必须晚于入住日期")

    if request.check_in_date < date.today():
        raise ParameterValidationException("入住日期不能早于今天")

    lock_name = f"booking:{request.cat_room_id}:{request.check_in_date}:{request.check_out_date}"

    async with redis_lock(lock_name, lock_timeout=30):
        logger.info(f"获取Redis锁成功: {lock_name}, user_id={user_id}")

        if not await check_room_availability(
            db,
            request.cat_room_id,
            request.check_in_date,
            request.check_out_date
        ):
            raise ConflictException(
                f"该猫屋在 {request.check_in_date} 至 {request.check_out_date} 期间已被预订",
                ErrorCode.CONFLICT
            )

        cat_room_result = await db.execute(
            select(CatRoom).where(
                and_(
                    CatRoom.id == request.cat_room_id,
                    CatRoom.status == CatRoomStatus.AVAILABLE
                )
            )
        )
        cat_room = cat_room_result.scalar_one_or_none()
        if not cat_room:
            raise NotFoundException(f"猫屋 {request.cat_room_id} 不可用", ErrorCode.NOT_FOUND)

        service_tuples = [(s.service_id, s.quantity) for s in request.addon_services]
        total_price = await calculate_total_price(
            db,
            request.cat_room_id,
            request.check_in_date,
            request.check_out_date,
            service_tuples
        )

        order_no = generate_order_no()
        verify_code = generate_verify_code()

        booking = Booking(
            order_no=order_no,
            user_id=user_id,
            cat_room_id=request.cat_room_id,
            check_in_date=request.check_in_date,
            check_out_date=request.check_out_date,
            cat_name=request.cat_name,
            cat_age=request.cat_age,
            cat_food_brand=request.cat_food_brand,
            special_requirements=request.special_requirements,
            status=BookingStatus.PENDING,
            total_price=total_price,
            verify_code=verify_code,
            version=1
        )

        db.add(booking)

        try:
            await db.flush()
        except IntegrityError as e:
            logger.error(f"创建预订唯一约束冲突: {e}")
            raise ConflictException(
                "该猫屋在此时间段已被预订，请选择其他时间",
                ErrorCode.DATABASE_INTEGRITY_ERROR
            )

        for service_item in request.addon_services:
            service_price = await get_service_price(db, service_item.service_id)
            booking_service = BookingService(
                booking_id=booking.id,
                service_id=service_item.service_id,
                quantity=service_item.quantity,
                price=service_price,
                status=BookingServiceStatus.PENDING
            )
            db.add(booking_service)

        _, payment_url = await payment_service.create_payment(
            db=db,
            order_no=order_no,
            amount=total_price,
            payment_method=request.payment_method,
            user_id=user_id
        )

        await db.flush()

        booking_result = await db.execute(
            select(Booking)
            .options(selectinload(Booking.booking_services))
            .where(Booking.id == booking.id)
        )
        booking = booking_result.scalar_one()

        booking_services_response = []
        for bs in booking.booking_services:
            service_name_result = await db.execute(
                select(Service.name).where(Service.id == bs.service_id)
            )
            service_name = service_name_result.scalar_one_or_none()
            booking_services_response.append(
                BookingServiceResponse(
                    id=bs.id,
                    booking_id=bs.booking_id,
                    service_id=bs.service_id,
                    service_name=service_name,
                    quantity=bs.quantity,
                    price=bs.price,
                    execute_time=bs.execute_time,
                    executor_id=bs.executor_id,
                    status=bs.status,
                    created_at=bs.created_at,
                    updated_at=bs.updated_at
                )
            )

        response = BookingResponse(
            id=booking.id,
            order_no=booking.order_no,
            user_id=booking.user_id,
            cat_room_id=booking.cat_room_id,
            cat_room_name=cat_room.name,
            check_in_date=booking.check_in_date,
            check_out_date=booking.check_out_date,
            cat_name=booking.cat_name,
            cat_age=booking.cat_age,
            cat_food_brand=booking.cat_food_brand,
            special_requirements=booking.special_requirements,
            status=booking.status,
            total_price=booking.total_price,
            verify_code=booking.verify_code,
            payment_url=payment_url,
            booking_services=booking_services_response,
            created_at=booking.created_at,
            updated_at=booking.updated_at
        )

        logger.info(f"预订创建成功: order_no={order_no}, user_id={user_id}, total={total_price}")

        return ApiResponse[BookingResponse](
            code=0,
            message="预订创建成功",
            data=response
        )


@router.get("", response_model=ApiResponse[PaginationResponse[BookingResponse]], summary="获取当前用户预订列表")
async def get_my_bookings(
    filter: BookingFilterRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的预订列表"""
    user_id = get_user_id(current_user)

    query = select(Booking).options(
        selectinload(Booking.booking_services),
        selectinload(Booking.cat_room)
    ).where(Booking.user_id == user_id)

    if filter.status:
        query = query.where(Booking.status == filter.status)
    if filter.start_date:
        query = query.where(Booking.check_in_date >= filter.start_date)
    if filter.end_date:
        query = query.where(Booking.check_out_date <= filter.end_date)

    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    query = query.order_by(Booking.created_at.desc())
    query = query.offset((filter.page - 1) * filter.page_size).limit(filter.page_size)

    result = await db.execute(query)
    bookings = result.scalars().all()

    items = []
    for booking in bookings:
        services_response = []
        for bs in booking.booking_services:
            service_name_result = await db.execute(
                select(Service.name).where(Service.id == bs.service_id)
            )
            service_name = service_name_result.scalar_one_or_none()
            services_response.append(
                BookingServiceResponse(
                    id=bs.id,
                    booking_id=bs.booking_id,
                    service_id=bs.service_id,
                    service_name=service_name,
                    quantity=bs.quantity,
                    price=bs.price,
                    execute_time=bs.execute_time,
                    executor_id=bs.executor_id,
                    status=bs.status,
                    created_at=bs.created_at,
                    updated_at=bs.updated_at
                )
            )

        items.append(
            BookingResponse(
                id=booking.id,
                order_no=booking.order_no,
                user_id=booking.user_id,
                cat_room_id=booking.cat_room_id,
                cat_room_name=booking.cat_room.name if booking.cat_room else None,
                check_in_date=booking.check_in_date,
                check_out_date=booking.check_out_date,
                cat_name=booking.cat_name,
                cat_age=booking.cat_age,
                cat_food_brand=booking.cat_food_brand,
                special_requirements=booking.special_requirements,
                status=booking.status,
                total_price=booking.total_price,
                verify_code=booking.verify_code,
                booking_services=services_response,
                created_at=booking.created_at,
                updated_at=booking.updated_at
            )
        )

    total_pages = (total + filter.page_size - 1) // filter.page_size

    return ApiResponse[PaginationResponse[BookingResponse]](
        code=0,
        message="success",
        data=PaginationResponse[BookingResponse](
            items=items,
            total=total,
            page=filter.page,
            page_size=filter.page_size,
            total_pages=total_pages
        )
    )


@router.get("/all", response_model=ApiResponse[PaginationResponse[BookingResponse]], summary="获取所有预订（员工权限）")
async def get_all_bookings(
    filter: BookingFilterRequest = Depends(),
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """获取所有预订列表（员工/管理员权限）"""
    query = select(Booking).options(
        selectinload(Booking.booking_services),
        selectinload(Booking.cat_room)
    )

    if filter.status:
        query = query.where(Booking.status == filter.status)
    if filter.start_date:
        query = query.where(Booking.check_in_date >= filter.start_date)
    if filter.end_date:
        query = query.where(Booking.check_out_date <= filter.end_date)

    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    query = query.order_by(Booking.created_at.desc())
    query = query.offset((filter.page - 1) * filter.page_size).limit(filter.page_size)

    result = await db.execute(query)
    bookings = result.scalars().all()

    items = []
    for booking in bookings:
        services_response = []
        for bs in booking.booking_services:
            service_name_result = await db.execute(
                select(Service.name).where(Service.id == bs.service_id)
            )
            service_name = service_name_result.scalar_one_or_none()
            services_response.append(
                BookingServiceResponse(
                    id=bs.id,
                    booking_id=bs.booking_id,
                    service_id=bs.service_id,
                    service_name=service_name,
                    quantity=bs.quantity,
                    price=bs.price,
                    execute_time=bs.execute_time,
                    executor_id=bs.executor_id,
                    status=bs.status,
                    created_at=bs.created_at,
                    updated_at=bs.updated_at
                )
            )

        items.append(
            BookingResponse(
                id=booking.id,
                order_no=booking.order_no,
                user_id=booking.user_id,
                cat_room_id=booking.cat_room_id,
                cat_room_name=booking.cat_room.name if booking.cat_room else None,
                check_in_date=booking.check_in_date,
                check_out_date=booking.check_out_date,
                cat_name=booking.cat_name,
                cat_age=booking.cat_age,
                cat_food_brand=booking.cat_food_brand,
                special_requirements=booking.special_requirements,
                status=booking.status,
                total_price=booking.total_price,
                verify_code=booking.verify_code,
                booking_services=services_response,
                created_at=booking.created_at,
                updated_at=booking.updated_at
            )
        )

    total_pages = (total + filter.page_size - 1) // filter.page_size

    return ApiResponse[PaginationResponse[BookingResponse]](
        code=0,
        message="success",
        data=PaginationResponse[BookingResponse](
            items=items,
            total=total,
            page=filter.page,
            page_size=filter.page_size,
            total_pages=total_pages
        )
    )


@router.get("/{booking_id}", response_model=ApiResponse[BookingResponse], summary="获取预订详情")
async def get_booking_detail(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取预订详情"""
    result = await db.execute(
        select(Booking)
        .options(
            selectinload(Booking.booking_services),
            selectinload(Booking.cat_room)
        )
        .where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise NotFoundException(f"预订 {booking_id} 不存在", ErrorCode.ORDER_NOT_FOUND)

    user_id = get_user_id(current_user)
    is_staff = current_user.role in ["admin", "staff"]

    if booking.user_id != user_id and not is_staff:
        raise ForbiddenException("无权查看该预订")

    services_response = []
    for bs in booking.booking_services:
        service_name_result = await db.execute(
            select(Service.name).where(Service.id == bs.service_id)
        )
        service_name = service_name_result.scalar_one_or_none()
        services_response.append(
            BookingServiceResponse(
                id=bs.id,
                booking_id=bs.booking_id,
                service_id=bs.service_id,
                service_name=service_name,
                quantity=bs.quantity,
                price=bs.price,
                execute_time=bs.execute_time,
                executor_id=bs.executor_id,
                status=bs.status,
                created_at=bs.created_at,
                updated_at=bs.updated_at
            )
        )

    response = BookingResponse(
        id=booking.id,
        order_no=booking.order_no,
        user_id=booking.user_id,
        cat_room_id=booking.cat_room_id,
        cat_room_name=booking.cat_room.name if booking.cat_room else None,
        check_in_date=booking.check_in_date,
        check_out_date=booking.check_out_date,
        cat_name=booking.cat_name,
        cat_age=booking.cat_age,
        cat_food_brand=booking.cat_food_brand,
        special_requirements=booking.special_requirements,
        status=booking.status,
        total_price=booking.total_price,
        verify_code=booking.verify_code if (booking.user_id == user_id or is_staff) else None,
        booking_services=services_response,
        created_at=booking.created_at,
        updated_at=booking.updated_at
    )

    return ApiResponse[BookingResponse](code=0, message="success", data=response)


@router.post("/{booking_id}/verify", response_model=ApiResponse[BookingResponse], summary="扫码核销（员工权限）")
async def verify_booking(
    booking_id: int,
    request: VerifyRequest,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """扫码核销，更新状态为checked_in（员工权限）"""
    current_version = None
    max_retries = 3

    for retry in range(max_retries):
        booking_result = await db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = booking_result.scalar_one_or_none()

        if not booking:
            raise NotFoundException(f"预订 {booking_id} 不存在", ErrorCode.ORDER_NOT_FOUND)

        if booking.status not in [BookingStatus.PAID, BookingStatus.CONFIRMED]:
            raise ConflictException(
                f"预订状态不允许核销，当前状态: {booking.status}",
                ErrorCode.ORDER_STATUS_ERROR
            )

        if booking.verify_code != request.verify_code:
            raise ParameterValidationException("核销码不正确")

        current_version = booking.version

        stmt = (
            update(Booking)
            .where(
                and_(
                    Booking.id == booking_id,
                    Booking.version == current_version
                )
            )
            .values(
                status=BookingStatus.CHECKED_IN,
                version=current_version + 1
            )
            .execution_options(synchronize_session=False)
        )

        result = await db.execute(stmt)

        if result.rowcount == 1:
            await db.flush()
            logger.info(f"预订核销成功: booking_id={booking_id}, operator={get_user_id(current_user)}")
            break
        else:
            if retry == max_retries - 1:
                raise ConflictException(
                    "并发冲突，核销失败，请重试",
                    ErrorCode.CONFLICT
                )
            await db.rollback()
            continue

    booking_result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.booking_services), selectinload(Booking.cat_room))
        .where(Booking.id == booking_id)
    )
    booking = booking_result.scalar_one()

    services_response = []
    for bs in booking.booking_services:
        service_name_result = await db.execute(
            select(Service.name).where(Service.id == bs.service_id)
        )
        service_name = service_name_result.scalar_one_or_none()
        services_response.append(
            BookingServiceResponse(
                id=bs.id,
                booking_id=bs.booking_id,
                service_id=bs.service_id,
                service_name=service_name,
                quantity=bs.quantity,
                price=bs.price,
                execute_time=bs.execute_time,
                executor_id=bs.executor_id,
                status=bs.status,
                created_at=bs.created_at,
                updated_at=bs.updated_at
            )
        )

    response = BookingResponse(
        id=booking.id,
        order_no=booking.order_no,
        user_id=booking.user_id,
        cat_room_id=booking.cat_room_id,
        cat_room_name=booking.cat_room.name if booking.cat_room else None,
        check_in_date=booking.check_in_date,
        check_out_date=booking.check_out_date,
        cat_name=booking.cat_name,
        cat_age=booking.cat_age,
        cat_food_brand=booking.cat_food_brand,
        special_requirements=booking.special_requirements,
        status=booking.status,
        total_price=booking.total_price,
        verify_code=booking.verify_code,
        booking_services=services_response,
        created_at=booking.created_at,
        updated_at=booking.updated_at
    )

    return ApiResponse[BookingResponse](
        code=0,
        message="核销成功",
        data=response
    )


@router.post("/{booking_id}/checkout", response_model=ApiResponse[BookingResponse], summary="退房（员工权限）")
async def checkout_booking(
    booking_id: int,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """退房（员工权限）"""
    current_version = None
    max_retries = 3

    for retry in range(max_retries):
        booking_result = await db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = booking_result.scalar_one_or_none()

        if not booking:
            raise NotFoundException(f"预订 {booking_id} 不存在", ErrorCode.ORDER_NOT_FOUND)

        if booking.status != BookingStatus.CHECKED_IN:
            raise ConflictException(
                f"预订状态不允许退房，当前状态: {booking.status}",
                ErrorCode.ORDER_STATUS_ERROR
            )

        current_version = booking.version

        stmt = (
            update(Booking)
            .where(
                and_(
                    Booking.id == booking_id,
                    Booking.version == current_version
                )
            )
            .values(
                status=BookingStatus.CHECKED_OUT,
                version=current_version + 1
            )
            .execution_options(synchronize_session=False)
        )

        result = await db.execute(stmt)

        if result.rowcount == 1:
            await db.flush()
            logger.info(f"预订退房成功: booking_id={booking_id}, operator={get_user_id(current_user)}")
            break
        else:
            if retry == max_retries - 1:
                raise ConflictException(
                    "并发冲突，退房失败，请重试",
                    ErrorCode.CONFLICT
                )
            await db.rollback()
            continue

    booking_result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.booking_services), selectinload(Booking.cat_room))
        .where(Booking.id == booking_id)
    )
    booking = booking_result.scalar_one()

    services_response = []
    for bs in booking.booking_services:
        service_name_result = await db.execute(
            select(Service.name).where(Service.id == bs.service_id)
        )
        service_name = service_name_result.scalar_one_or_none()
        services_response.append(
            BookingServiceResponse(
                id=bs.id,
                booking_id=bs.booking_id,
                service_id=bs.service_id,
                service_name=service_name,
                quantity=bs.quantity,
                price=bs.price,
                execute_time=bs.execute_time,
                executor_id=bs.executor_id,
                status=bs.status,
                created_at=bs.created_at,
                updated_at=bs.updated_at
            )
        )

    response = BookingResponse(
        id=booking.id,
        order_no=booking.order_no,
        user_id=booking.user_id,
        cat_room_id=booking.cat_room_id,
        cat_room_name=booking.cat_room.name if booking.cat_room else None,
        check_in_date=booking.check_in_date,
        check_out_date=booking.check_out_date,
        cat_name=booking.cat_name,
        cat_age=booking.cat_age,
        cat_food_brand=booking.cat_food_brand,
        special_requirements=booking.special_requirements,
        status=booking.status,
        total_price=booking.total_price,
        verify_code=booking.verify_code,
        booking_services=services_response,
        created_at=booking.created_at,
        updated_at=booking.updated_at
    )

    return ApiResponse[BookingResponse](
        code=0,
        message="退房成功",
        data=response
    )


@router.post("/{booking_id}/add-service", response_model=ApiResponse[BookingServiceResponse], summary="入住期间加购服务")
async def add_service_to_booking(
    booking_id: int,
    request: AddServiceRequest,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """入住期间加购服务（员工权限）"""
    booking_result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = booking_result.scalar_one_or_none()

    if not booking:
        raise NotFoundException(f"预订 {booking_id} 不存在", ErrorCode.ORDER_NOT_FOUND)

    if booking.status != BookingStatus.CHECKED_IN:
        raise ConflictException(
            f"只有入住中的预订可以加购服务，当前状态: {booking.status}",
            ErrorCode.ORDER_STATUS_ERROR
        )

    service_price = await get_service_price(db, request.service_id)
    service_name_result = await db.execute(
        select(Service.name).where(Service.id == request.service_id)
    )
    service_name = service_name_result.scalar_one_or_none()

    booking_service = BookingService(
        booking_id=booking_id,
        service_id=request.service_id,
        quantity=request.quantity,
        price=service_price,
        execute_time=request.execute_time or datetime.now(),
        executor_id=get_user_id(current_user),
        status=BookingServiceStatus.COMPLETED
    )

    db.add(booking_service)
    await db.flush()

    additional_amount = service_price * request.quantity
    booking.total_price += additional_amount
    await db.flush()

    logger.info(
        f"预订加购服务成功: booking_id={booking_id}, service_id={request.service_id}, "
        f"quantity={request.quantity}, amount={additional_amount}, operator={get_user_id(current_user)}"
    )

    response = BookingServiceResponse(
        id=booking_service.id,
        booking_id=booking_service.booking_id,
        service_id=booking_service.service_id,
        service_name=service_name,
        quantity=booking_service.quantity,
        price=booking_service.price,
        execute_time=booking_service.execute_time,
        executor_id=booking_service.executor_id,
        status=booking_service.status,
        created_at=booking_service.created_at,
        updated_at=booking_service.updated_at
    )

    return ApiResponse[BookingServiceResponse](
        code=0,
        message="服务加购成功",
        data=response
    )


@router.post("/{booking_id}/cancel", response_model=ApiResponse[RefundAmountResponse], summary="取消预订")
async def cancel_booking(
    booking_id: int,
    request: CancelBookingRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """取消预订，按退款规则计算退款金额"""
    booking_result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = booking_result.scalar_one_or_none()

    if not booking:
        raise NotFoundException(f"预订 {booking_id} 不存在", ErrorCode.ORDER_NOT_FOUND)

    user_id = get_user_id(current_user)
    is_staff = current_user.role in ["admin", "staff"]

    if booking.user_id != user_id and not is_staff:
        raise ForbiddenException("无权取消该预订")

    cancel_time = datetime.now()
    refund_amount, refund_fee, refund_rule, can_refund, reason = calculate_refund_amount(booking, cancel_time)

    if not can_refund:
        raise ConflictException(reason or "不允许退款", ErrorCode.REFUND_NOT_ALLOWED)

    max_retries = 3
    for retry in range(max_retries):
        current_version = booking.version

        stmt = (
            update(Booking)
            .where(
                and_(
                    Booking.id == booking_id,
                    Booking.version == current_version
                )
            )
            .values(
                status=BookingStatus.CANCELLED,
                version=current_version + 1
            )
            .execution_options(synchronize_session=False)
        )

        result = await db.execute(stmt)

        if result.rowcount == 1:
            break
        else:
            if retry == max_retries - 1:
                raise ConflictException(
                    "并发冲突，取消失败，请重试",
                    ErrorCode.CONFLICT
                )
            booking_result = await db.execute(
                select(Booking).where(Booking.id == booking_id)
            )
            booking = booking_result.scalar_one_or_none()
            continue

    if refund_amount > 0:
        refund = Refund(
            order_no=booking.order_no,
            refund_amount=refund_amount,
            refund_reason=request.refund_reason,
            status=RefundStatus.COMPLETED,
            approver_id=get_user_id(current_user) if is_staff else None
        )
        db.add(refund)

        await payment_service.refund_payment(db, booking.order_no, refund_amount)

    await db.flush()

    logger.info(
        f"预订取消成功: booking_id={booking_id}, user_id={user_id}, "
        f"refund_amount={refund_amount}, fee={refund_fee}"
    )

    response = RefundAmountResponse(
        order_no=booking.order_no,
        original_amount=booking.total_price,
        refund_amount=refund_amount,
        refund_fee=refund_fee,
        refund_rule=refund_rule,
        can_refund=True
    )

    return ApiResponse[RefundAmountResponse](
        code=0,
        message="取消成功，退款处理中",
        data=response
    )


@router.get("/{booking_id}/qrcode", response_model=ApiResponse[BookingQRCodeResponse], summary="获取预订核销码二维码")
async def get_booking_qrcode(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取预订核销码二维码"""
    booking_result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = booking_result.scalar_one_or_none()

    if not booking:
        raise NotFoundException(f"预订 {booking_id} 不存在", ErrorCode.ORDER_NOT_FOUND)

    user_id = get_user_id(current_user)
    is_staff = current_user.role in ["admin", "staff"]

    if booking.user_id != user_id and not is_staff:
        raise ForbiddenException("无权查看该预订的二维码")

    if booking.status in [BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT, BookingStatus.CANCELLED, BookingStatus.REFUNDED]:
        raise ConflictException(
            f"当前预订状态不支持获取核销码: {booking.status}",
            ErrorCode.ORDER_STATUS_ERROR
        )

    qr_data = f"BOOKING:{booking.id}:{booking.verify_code}:{booking.order_no}"
    qr_code_base64 = generate_qr_code_base64(qr_data)

    response = BookingQRCodeResponse(
        booking_id=booking.id,
        verify_code=booking.verify_code,
        qr_code_base64=qr_code_base64
    )

    return ApiResponse[BookingQRCodeResponse](
        code=0,
        message="success",
        data=response
    )


@router.get("/{booking_id}/refund", response_model=ApiResponse[RefundAmountResponse], summary="获取可退款金额")
async def get_refund_amount(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """提前计算可退款金额"""
    booking_result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = booking_result.scalar_one_or_none()

    if not booking:
        raise NotFoundException(f"预订 {booking_id} 不存在", ErrorCode.ORDER_NOT_FOUND)

    user_id = get_user_id(current_user)
    is_staff = current_user.role in ["admin", "staff"]

    if booking.user_id != user_id and not is_staff:
        raise ForbiddenException("无权查看该预订的退款信息")

    cancel_time = datetime.now()
    refund_amount, refund_fee, refund_rule, can_refund, reason = calculate_refund_amount(booking, cancel_time)

    response = RefundAmountResponse(
        order_no=booking.order_no,
        original_amount=booking.total_price,
        refund_amount=refund_amount,
        refund_fee=refund_fee,
        refund_rule=refund_rule,
        can_refund=can_refund,
        reason=reason
    )

    return ApiResponse[RefundAmountResponse](
        code=0,
        message="success",
        data=response
    )
