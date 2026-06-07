import logging
from datetime import datetime
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_db, get_current_active_user
from app.core.errors import (
    BusinessException,
    ErrorCode,
    NotFoundException,
    ConflictException,
    ParameterValidationException
)
from app.utils.payment import payment_service
from app.models.member import Member
from app.models.point_record import PointRecord, PointType
from app.models.payment import PaymentMethod
from app.models.user import User
from app.schemas import (
    ApiResponse,
    PaginationResponse,
    PaginationRequest,
    MemberResponse as SchemaMemberResponse,
    MemberRecharge,
    PointsRecord,
)
from app.schemas.member import (
    MemberResponse,
    MemberRechargeRequest,
    RechargeResponse,
    PointRecordFilterRequest,
    PointRecordResponse,
    PointExchangeRequest,
    PointExchangeResponse
)
from app.utils.redis_lock import redis_lock

logger = logging.getLogger(__name__)

router = APIRouter()


def get_user_id(user: User) -> int:
    return user.id


async def get_or_create_member(db: AsyncSession, user_id: int) -> Member:
    """获取或创建会员记录"""
    result = await db.execute(
        select(Member).where(Member.user_id == user_id)
    )
    member = result.scalar_one_or_none()

    if not member:
        member = Member(
            user_id=user_id,
            level=1,
            points=0,
            balance=Decimal(0),
            version=1
        )
        db.add(member)
        await db.flush()
        logger.info(f"为用户创建会员账户: user_id={user_id}")

    return member


async def add_point_record(
    db: AsyncSession,
    member_id: int,
    type: PointType,
    points: int,
    description: str,
    related_order_no: Optional[str] = None
) -> PointRecord:
    """
    添加积分记录（使用乐观锁确保原子性）

    并发控制：使用version字段确保积分余额更新的原子性
    """
    max_retries = 3

    for retry in range(max_retries):
        member_result = await db.execute(
            select(Member).where(Member.id == member_id)
        )
        member = member_result.scalar_one_or_none()

        if not member:
            raise NotFoundException(f"会员 {member_id} 不存在", ErrorCode.NOT_FOUND)

        balance_before = member.points

        if type in [PointType.SPEND, PointType.EXCHANGE, PointType.EXPIRED]:
            if balance_before < points:
                raise ConflictException(
                    f"积分不足，当前积分: {balance_before}，需要: {points}",
                    ErrorCode.INSUFFICIENT_BALANCE
                )
            balance_after = balance_before - points
        else:
            balance_after = balance_before + points

        current_version = member.version

        stmt = (
            update(Member)
            .where(
                and_(
                    Member.id == member_id,
                    Member.version == current_version
                )
            )
            .values(
                points=balance_after,
                version=current_version + 1
            )
            .execution_options(synchronize_session=False)
        )

        result = await db.execute(stmt)

        if result.rowcount == 1:
            point_record = PointRecord(
                member_id=member_id,
                type=type,
                points=points,
                description=description,
                balance_before=balance_before,
                balance_after=balance_after,
                related_order_no=related_order_no
            )
            db.add(point_record)
            await db.flush()

            logger.info(
                f"积分记录添加成功: member_id={member_id}, type={type}, "
                f"points={points}, balance={balance_after}"
            )
            return point_record
        else:
            if retry == max_retries - 1:
                raise ConflictException(
                    "并发冲突，积分操作失败，请重试",
                    ErrorCode.CONFLICT
                )
            await db.rollback()
            continue

    raise ConflictException("积分操作失败，请重试", ErrorCode.CONFLICT)


@router.get("/me", response_model=ApiResponse[MemberResponse], summary="获取当前会员信息")
async def get_member_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前登录用户的会员信息"""
    user_id = get_user_id(current_user)
    member = await get_or_create_member(db, user_id)

    response = MemberResponse(
        id=member.id,
        user_id=member.user_id,
        level=member.level,
        points=member.points,
        balance=member.balance,
        valid_until=member.valid_until,
        created_at=member.created_at,
        updated_at=member.updated_at
    )

    return ApiResponse[MemberResponse](code=0, message="success", data=response)


@router.post("/recharge", response_model=ApiResponse[RechargeResponse], summary="会员充值")
async def member_recharge(
    request: MemberRechargeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    会员充值（使用Redis分布式锁防止并发充值）

    并发控制：使用Redis分布式锁确保同一用户不会并发充值
    """
    user_id = get_user_id(current_user)
    lock_name = f"member_recharge:{user_id}"

    async with redis_lock(lock_name, lock_timeout=30):
        member = await get_or_create_member(db, user_id)

        balance_before = member.balance
        balance_after = balance_before + request.amount

        max_retries = 3
        for retry in range(max_retries):
            current_version = member.version

            stmt = (
                update(Member)
                .where(
                    and_(
                        Member.id == member.id,
                        Member.version == current_version
                    )
                )
                .values(
                    balance=balance_after,
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
                        "并发冲突，充值失败，请重试",
                        ErrorCode.CONFLICT
                    )
                member_result = await db.execute(
                    select(Member).where(Member.id == member.id)
                )
                member = member_result.scalar_one()
                balance_before = member.balance
                balance_after = balance_before + request.amount
                continue

        payment_method = PaymentMethod(request.payment_method)
        order_no = f"RECHARGE{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id}"

        _, payment_url = await payment_service.create_payment(
            db=db,
            order_no=order_no,
            amount=request.amount,
            payment_method=payment_method,
            user_id=user_id
        )

        await db.flush()

        logger.info(
            f"会员充值请求创建成功: user_id={user_id}, amount={request.amount}, "
            f"balance_before={balance_before}, balance_after={balance_after}"
        )

        response = RechargeResponse(
            member_id=member.id,
            amount=request.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            payment_url=payment_url,
            status="pending",
            created_at=datetime.now()
        )

        return ApiResponse[RechargeResponse](
            code=0,
            message="充值请求已提交，请完成支付",
            data=response
        )


@router.get("/points", response_model=ApiResponse[PaginationResponse[PointRecordResponse]], summary="获取积分记录")
async def get_point_records(
    filter: PointRecordFilterRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的积分记录"""
    user_id = get_user_id(current_user)

    member_result = await db.execute(
        select(Member).where(Member.user_id == user_id)
    )
    member = member_result.scalar_one_or_none()

    if not member:
        return ApiResponse[PaginationResponse[PointRecordResponse]](
            code=0,
            message="success",
            data=PaginationResponse[PointRecordResponse](
                items=[],
                total=0,
                page=filter.page,
                page_size=filter.page_size,
                total_pages=0
            )
        )

    query = select(PointRecord).where(PointRecord.member_id == member.id)

    if filter.type:
        query = query.where(PointRecord.type == filter.type)
    if filter.start_date:
        query = query.where(PointRecord.created_at >= filter.start_date)
    if filter.end_date:
        query = query.where(PointRecord.created_at <= filter.end_date)

    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    query = query.order_by(PointRecord.created_at.desc())
    query = query.offset((filter.page - 1) * filter.page_size).limit(filter.page_size)

    result = await db.execute(query)
    records = result.scalars().all()

    items = [
        PointRecordResponse(
            id=r.id,
            member_id=r.member_id,
            type=r.type,
            points=r.points,
            description=r.description,
            balance_before=r.balance_before,
            balance_after=r.balance_after,
            related_order_no=r.related_order_no,
            created_at=r.created_at
        )
        for r in records
    ]

    total_pages = (total + filter.page_size - 1) // filter.page_size

    return ApiResponse[PaginationResponse[PointRecordResponse]](
        code=0,
        message="success",
        data=PaginationResponse[PointRecordResponse](
            items=items,
            total=total,
            page=filter.page,
            page_size=filter.page_size,
            total_pages=total_pages
        )
    )


@router.post("/points/exchange", response_model=ApiResponse[PointExchangeResponse], summary="积分兑换")
async def exchange_points(
    request: PointExchangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    积分兑换（使用乐观锁确保原子性）

    并发控制：
    1. Redis分布式锁防止同一用户并发兑换
    2. 数据库乐观锁确保积分余额更新原子性
    """
    user_id = get_user_id(current_user)
    lock_name = f"member_points_exchange:{user_id}"

    async with redis_lock(lock_name, lock_timeout=30):
        member_result = await db.execute(
            select(Member).where(Member.user_id == user_id)
        )
        member = member_result.scalar_one_or_none()

        if not member:
            raise NotFoundException("会员账户不存在", ErrorCode.NOT_FOUND)

        points_before = member.points
        if points_before < request.points:
            raise ConflictException(
                f"积分不足，当前积分: {points_before}，需要: {request.points}",
                ErrorCode.INSUFFICIENT_BALANCE
            )

        description = f"积分兑换: {request.exchange_item}"

        point_record = await add_point_record(
            db=db,
            member_id=member.id,
            type=PointType.EXCHANGE,
            points=request.points,
            description=description
        )

        await db.flush()

        logger.info(
            f"积分兑换成功: user_id={user_id}, points={request.points}, "
            f"item={request.exchange_item}, balance_before={points_before}, "
            f"balance_after={point_record.balance_after}"
        )

        response = PointExchangeResponse(
            member_id=member.id,
            points=request.points,
            exchange_item=request.exchange_item,
            points_before=points_before,
            points_after=point_record.balance_after,
            status="success",
            created_at=datetime.now()
        )

        return ApiResponse[PointExchangeResponse](
            code=0,
            message="兑换成功",
            data=response
        )
