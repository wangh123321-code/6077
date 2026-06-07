import logging
import uuid
import json
from typing import Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.config.settings import settings
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.booking import Booking, BookingStatus
from app.models.member import Member
from app.core.errors import (
    BusinessException,
    ErrorCode,
    NotFoundException,
    ConflictException
)
from app.database.session import get_db

logger = logging.getLogger(__name__)


class PaymentService:
    """支付服务类，提供模拟支付、支付链接生成和回调处理功能"""

    def __init__(self):
        self.base_url = "https://api.payment-gateway.com"
        self.timeout = 30.0

    async def create_payment(
        self,
        db: AsyncSession,
        order_no: str,
        amount: Decimal,
        payment_method: PaymentMethod,
        user_id: Optional[int] = None
    ) -> Tuple[Payment, str]:
        """
        创建支付订单，生成支付链接

        Args:
            db: 数据库会话
            order_no: 订单号
            amount: 支付金额
            payment_method: 支付方式
            user_id: 用户ID

        Returns:
            (Payment对象, 支付链接)

        Raises:
            NotFoundException: 订单不存在
            ConflictException: 订单已支付
        """
        result = await db.execute(
            select(Booking).where(Booking.order_no == order_no)
        )
        booking = result.scalar_one_or_none()

        if not booking:
            raise NotFoundException(f"订单 {order_no} 不存在", ErrorCode.ORDER_NOT_FOUND)

        if booking.status in [BookingStatus.PAID, BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT]:
            raise ConflictException(f"订单 {order_no} 已支付", ErrorCode.ORDER_STATUS_ERROR)

        existing_payment_result = await db.execute(
            select(Payment).where(
                and_(
                    Payment.order_no == order_no,
                    Payment.status == PaymentStatus.PENDING
                )
            )
        )
        existing_payment = existing_payment_result.scalar_one_or_none()

        if existing_payment:
            payment_url = self._generate_payment_url(
                order_no,
                amount,
                payment_method,
                existing_payment.transaction_id or str(uuid.uuid4())
            )
            return existing_payment, payment_url

        transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

        payment = Payment(
            order_no=order_no,
            payment_method=payment_method,
            amount=amount,
            transaction_id=transaction_id,
            status=PaymentStatus.PENDING
        )

        db.add(payment)
        await db.flush()

        payment_url = self._generate_payment_url(order_no, amount, payment_method, transaction_id)

        logger.info(f"创建支付订单成功: order_no={order_no}, amount={amount}, method={payment_method}")

        return payment, payment_url

    def _generate_payment_url(
        self,
        order_no: str,
        amount: Decimal,
        payment_method: PaymentMethod,
        transaction_id: str
    ) -> str:
        """
        生成模拟支付链接

        Args:
            order_no: 订单号
            amount: 支付金额
            payment_method: 支付方式
            transaction_id: 交易ID

        Returns:
            支付链接URL
        """
        import urllib.parse

        params = {
            "order_no": order_no,
            "amount": str(amount),
            "method": payment_method.value,
            "transaction_id": transaction_id,
            "timestamp": str(int(datetime.now().timestamp())),
            "sign": self._generate_sign(order_no, amount, transaction_id)
        }

        base_url = "http://localhost:8000" if settings.ENV == "development" else self.base_url
        query_string = urllib.parse.urlencode(params)

        return f"{base_url}/api/v1/payments/mock?{query_string}"

    def _generate_sign(self, order_no: str, amount: Decimal, transaction_id: str) -> str:
        """
        生成签名（模拟）

        Args:
            order_no: 订单号
            amount: 金额
            transaction_id: 交易ID

        Returns:
            签名字符串
        """
        import hashlib

        sign_str = f"{order_no}{amount}{transaction_id}{settings.JWT_SECRET_KEY}"
        return hashlib.md5(sign_str.encode()).hexdigest()

    def verify_sign(self, order_no: str, amount: Decimal, transaction_id: str, sign: str) -> bool:
        """
        验证签名

        Args:
            order_no: 订单号
            amount: 金额
            transaction_id: 交易ID
            sign: 待验证的签名

        Returns:
            True表示验证通过，False表示验证失败
        """
        expected_sign = self._generate_sign(order_no, amount, transaction_id)
        return expected_sign == sign

    async def process_payment_callback(
        self,
        db: AsyncSession,
        order_no: str,
        transaction_id: str,
        amount: Decimal,
        status: str,
        payment_method: str,
        raw_data: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """
        处理支付回调

        Args:
            db: 数据库会话
            order_no: 订单号
            transaction_id: 交易ID
            amount: 支付金额
            status: 支付状态
            payment_method: 支付方式
            raw_data: 原始回调数据

        Returns:
            更新后的Payment对象

        Raises:
            NotFoundException: 支付记录不存在
            ConflictException: 支付状态冲突
        """
        result = await db.execute(
            select(Payment).where(Payment.transaction_id == transaction_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise NotFoundException(f"支付记录不存在: transaction_id={transaction_id}")

        if payment.status == PaymentStatus.SUCCESS:
            logger.warning(f"支付已成功，忽略重复回调: transaction_id={transaction_id}")
            return payment

        if payment.status == PaymentStatus.REFUNDED:
            raise ConflictException(f"支付已退款，无法更新状态: transaction_id={transaction_id}")

        if status.lower() in ["success", "paid", "completed"]:
            payment.status = PaymentStatus.SUCCESS

            booking_result = await db.execute(
                select(Booking).where(Booking.order_no == order_no)
            )
            booking = booking_result.scalar_one_or_none()

            if booking and booking.status == BookingStatus.PENDING:
                booking.status = BookingStatus.PAID
                logger.info(f"订单状态更新为已支付: order_no={order_no}")

                points_earned = int(amount)
                await self._add_member_points(db, booking.user_id, points_earned, order_no)

        elif status.lower() in ["failed", "fail", "error"]:
            payment.status = PaymentStatus.FAILED

            booking_result = await db.execute(
                select(Booking).where(Booking.order_no == order_no)
            )
            booking = booking_result.scalar_one_or_none()

            if booking and booking.status == BookingStatus.PENDING:
                booking.status = BookingStatus.CANCELLED
                logger.info(f"支付失败，订单已取消: order_no={order_no}")

        payment.callback_data = json.dumps(raw_data) if raw_data else None

        await db.flush()

        logger.info(
            f"支付回调处理完成: order_no={order_no}, "
            f"transaction_id={transaction_id}, status={payment.status}"
        )

        return payment

    async def _add_member_points(
        self,
        db: AsyncSession,
        user_id: int,
        points: int,
        order_no: str
    ) -> Optional[Member]:
        """
        为会员添加积分

        Args:
            db: 数据库会话
            user_id: 用户ID
            points: 积分数
            order_no: 关联订单号

        Returns:
            更新后的Member对象，如果用户不是会员则返回None
        """
        result = await db.execute(
            select(Member).where(Member.user_id == user_id)
        )
        member = result.scalar_one_or_none()

        if member:
            member.points += points
            await db.flush()
            logger.info(f"会员积分增加: user_id={user_id}, points={points}, order_no={order_no}")
            return member

        logger.info(f"用户不是会员，跳过积分发放: user_id={user_id}")
        return None

    async def refund_payment(
        self,
        db: AsyncSession,
        order_no: str,
        refund_amount: Optional[Decimal] = None
    ) -> Payment:
        """
        处理退款

        Args:
            db: 数据库会话
            order_no: 订单号
            refund_amount: 退款金额，None表示全额退款

        Returns:
            更新后的Payment对象

        Raises:
            NotFoundException: 支付记录不存在
            ConflictException: 支付状态不允许退款
        """
        result = await db.execute(
            select(Payment).where(
                and_(
                    Payment.order_no == order_no,
                    Payment.status == PaymentStatus.SUCCESS
                )
            )
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise NotFoundException(
                f"未找到可退款的支付记录: order_no={order_no}",
                ErrorCode.REFUND_NOT_ALLOWED
            )

        refund_amount = refund_amount or payment.amount

        if refund_amount > payment.amount:
            raise ConflictException(
                f"退款金额超过支付金额: refund={refund_amount}, paid={payment.amount}",
                ErrorCode.REFUND_AMOUNT_EXCEEDED
            )

        payment.status = PaymentStatus.REFUNDED

        booking_result = await db.execute(
            select(Booking).where(Booking.order_no == order_no)
        )
        booking = booking_result.scalar_one_or_none()

        if booking:
            booking.status = BookingStatus.REFUNDED

        await db.flush()

        logger.info(
            f"退款处理完成: order_no={order_no}, "
            f"refund_amount={refund_amount}, original_amount={payment.amount}"
        )

        return payment

    async def mock_payment_complete(
        self,
        db: AsyncSession,
        order_no: str,
        success: bool = True
    ) -> Payment:
        """
        模拟支付完成（用于开发测试）

        Args:
            db: 数据库会话
            order_no: 订单号
            success: 是否支付成功

        Returns:
            更新后的Payment对象
        """
        result = await db.execute(
            select(Payment).where(
                and_(
                    Payment.order_no == order_no,
                    Payment.status == PaymentStatus.PENDING
                )
            )
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise NotFoundException(f"未找到待支付的订单: order_no={order_no}")

        status = "success" if success else "failed"

        return await self.process_payment_callback(
            db=db,
            order_no=order_no,
            transaction_id=payment.transaction_id or str(uuid.uuid4()),
            amount=payment.amount,
            status=status,
            payment_method=payment.payment_method.value,
            raw_data={"mock": True, "success": success}
        )


payment_service = PaymentService()
