from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.config.settings import settings
from app.core.errors import (
    ConflictException,
    NotFoundException,
    UnauthorizedException,
    ErrorCode,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    hash_password,
)
from app.models.user import User, UserRole
from app.schemas import ApiResponse, UserCreate, UserLogin, UserResponse, TokenResponse

router = APIRouter()


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(User).where(User.phone == login_data.phone))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException(
            message="用户不存在",
            code=ErrorCode.USER_NOT_FOUND,
        )

    if not verify_password(login_data.password, user.password_hash):
        raise UnauthorizedException(
            message="手机号或密码错误",
            code=ErrorCode.INVALID_CREDENTIALS,
        )

    role_map = {
        UserRole.USER: "user",
        UserRole.STAFF: "operator",
        UserRole.ADMIN: "admin",
    }

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        role=role_map.get(user.role, "user"),
        expires_delta=access_token_expires,
    )

    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        subject=user.id,
        role=role_map.get(user.role, "user"),
        expires_delta=refresh_token_expires,
    )

    return ApiResponse(
        code=0,
        message="success",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
    )


@router.post("/register", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(User).where(User.phone == user_data.phone))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise ConflictException(
            message="该手机号已被注册",
            code=ErrorCode.PHONE_ALREADY_EXISTS,
        )

    hashed_password = hash_password(user_data.password)

    new_user = User(
        phone=user_data.phone,
        password_hash=hashed_password,
        nickname=user_data.nickname,
        avatar=user_data.avatar,
        role=UserRole.USER,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return ApiResponse(
        code=0,
        message="注册成功",
        data=UserResponse.model_validate(new_user),
    )


@router.post("/logout", response_model=ApiResponse[dict])
async def logout(
    current_user: User = Depends(get_current_user),
) -> Any:
    return ApiResponse(
        code=0,
        message="登出成功",
        data={},
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    return ApiResponse(
        code=0,
        message="success",
        data=UserResponse.model_validate(current_user),
    )
