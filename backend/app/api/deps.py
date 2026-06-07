from typing import Optional
from datetime import datetime, timezone

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from app.config.settings import settings
from app.database.session import get_db
from app.models.user import User, UserRole
from app.core.errors import (
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    ErrorCode,
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}/auth/login",
    scheme_name="JWT",
    auto_error=False,
)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise UnauthorizedException(
            message="未提供认证令牌",
            code=ErrorCode.INVALID_TOKEN,
        )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
        )

        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException(
                message="无效的认证令牌",
                code=ErrorCode.INVALID_TOKEN,
            )

        exp = payload.get("exp")
        if exp is not None and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise UnauthorizedException(
                message="认证令牌已过期",
                code=ErrorCode.TOKEN_EXPIRED,
            )

    except JWTError:
        raise UnauthorizedException(
            message="无效的认证令牌",
            code=ErrorCode.INVALID_TOKEN,
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException(
            message="用户不存在",
            code=ErrorCode.USER_NOT_FOUND,
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException(message="需要管理员权限")
    return current_user


async def get_current_staff(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise ForbiddenException(message="需要员工权限")
    return current_user
