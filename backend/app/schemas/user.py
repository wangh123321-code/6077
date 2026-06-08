from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.models.user import UserRole


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    phone: str = Field(..., description="手机号", min_length=11, max_length=20)
    nickname: Optional[str] = Field(None, description="昵称", max_length=50)
    avatar: Optional[str] = Field(None, description="头像URL", max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., description="密码", min_length=6, max_length=50)


RegisterRequest = UserCreate


class UserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nickname: Optional[str] = Field(None, description="昵称", max_length=50)
    avatar: Optional[str] = Field(None, description="头像URL", max_length=255)
    password: Optional[str] = Field(None, description="密码", min_length=6, max_length=50)


class UserResponse(UserBase):
    id: int
    role: UserRole
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    phone: str = Field(..., description="手机号", min_length=11, max_length=20)
    password: str = Field(..., description="密码", min_length=6, max_length=50)


LoginRequest = UserLogin


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
