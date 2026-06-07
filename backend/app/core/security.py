"""
安全认证模块
提供JWT认证、密码哈希、权限验证等安全功能
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
from enum import Enum

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.config.settings import settings
from app.database.session import get_db


# ========== 密码哈希配置 ==========
# 使用bcrypt算法进行密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ========== OAuth2配置 ==========
# OAuth2密码模式，指定token获取的URL
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}/auth/login",
    scheme_name="JWT"
)


# ========== 权限角色枚举 ==========
class Role(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"        # 管理员
    USER = "user"          # 普通用户
    GUEST = "guest"        # 访客
    OPERATOR = "operator"  # 运营人员


# ========== Token类型枚举 ==========
class TokenType(str, Enum):
    """Token类型枚举"""
    ACCESS = "access"    # 访问令牌
    REFRESH = "refresh"  # 刷新令牌


# ========== Token数据模型 ==========
class TokenPayload(BaseModel):
    """Token载荷数据模型"""
    sub: str                    # 用户标识（通常是用户ID）
    type: TokenType             # Token类型
    role: Role                  # 用户角色
    exp: datetime               # 过期时间
    iat: datetime               # 签发时间
    jti: str                    # Token唯一标识
    iss: str = settings.JWT_ISSUER   # 签发者
    aud: str = settings.JWT_AUDIENCE # 接收者


# ========== 密码哈希相关函数 ==========
def hash_password(password: str) -> str:
    """
    对密码进行哈希处理

    Args:
        password: 明文密码

    Returns:
        哈希后的密码字符串
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        True表示匹配，False表示不匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


# ========== JWT Token相关函数 ==========
def create_access_token(
    subject: Union[str, Any],
    role: Role = Role.USER,
    expires_delta: Optional[timedelta] = None,
    jti: Optional[str] = None
) -> str:
    """
    创建访问令牌（Access Token）

    Args:
        subject: 用户标识，通常是用户ID
        role: 用户角色
        expires_delta: 过期时间增量，不传则使用配置的默认值
        jti: Token唯一标识，不传则自动生成

    Returns:
        JWT Token字符串
    """
    import uuid

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),
        "type": TokenType.ACCESS.value,
        "role": role.value,
        "exp": expire,
        "iat": now,
        "jti": jti or str(uuid.uuid4()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE
    }

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(
    subject: Union[str, Any],
    role: Role = Role.USER,
    expires_delta: Optional[timedelta] = None,
    jti: Optional[str] = None
) -> str:
    """
    创建刷新令牌（Refresh Token）

    Args:
        subject: 用户标识，通常是用户ID
        role: 用户角色
        expires_delta: 过期时间增量，不传则使用配置的默认值
        jti: Token唯一标识，不传则自动生成

    Returns:
        JWT Token字符串
    """
    import uuid

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": str(subject),
        "type": TokenType.REFRESH.value,
        "role": role.value,
        "exp": expire,
        "iat": now,
        "jti": jti or str(uuid.uuid4()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE
    }

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str, token_type: Optional[TokenType] = None) -> TokenPayload:
    """
    解码并验证JWT Token

    Args:
        token: JWT Token字符串
        token_type: 指定Token类型验证，不传则不验证类型

    Returns:
        TokenPayload对象，包含Token的载荷数据

    Raises:
        HTTPException: Token无效、过期或类型不匹配时抛出
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE
        )

        # 验证Token类型
        if token_type and payload.get("type") != token_type.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token类型错误，需要{token_type.value}类型",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 转换时间戳为datetime对象
        payload["exp"] = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        payload["iat"] = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

        return TokenPayload(**payload)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token验证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ========== 认证依赖 ==========
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> TokenPayload:
    """
    获取当前认证用户（依赖注入函数）

    验证Token有效性并返回用户信息

    Args:
        token: OAuth2 Token
        db: 数据库会话

    Returns:
        TokenPayload对象，包含当前用户信息

    使用示例:
        @app.get("/users/me")
        async def get_current_user_info(current_user: TokenPayload = Depends(get_current_user)):
            ...
    """
    token_data = decode_token(token, token_type=TokenType.ACCESS)
    return token_data


# ========== 权限验证依赖 ==========
class RoleRequired:
    """
    角色权限验证依赖类

    用于验证用户是否拥有指定的角色权限

    使用示例:
        @app.get("/admin")
        async def admin_only(current_user: TokenPayload = Depends(RoleRequired(Role.ADMIN))):
            ...
    """

    def __init__(self, required_roles: Union[Role, list[Role]]):
        """
        初始化权限验证器

        Args:
            required_roles: 需要的角色，可以是单个角色或角色列表
        """
        if isinstance(required_roles, Role):
            self.required_roles = [required_roles]
        else:
            self.required_roles = required_roles

    def __call__(self, current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        """
        验证用户角色权限

        Args:
            current_user: 当前认证用户

        Returns:
            TokenPayload对象（验证通过时）

        Raises:
            HTTPException: 权限不足时抛出
        """
        if current_user.role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，无法访问该资源",
            )
        return current_user


# ========== 便捷权限依赖 ==========
# 管理员权限
admin_required = RoleRequired(Role.ADMIN)
# 运营人员权限（包含管理员）
operator_required = RoleRequired([Role.ADMIN, Role.OPERATOR])
# 普通用户权限（包含管理员和运营人员）
user_required = RoleRequired([Role.ADMIN, Role.OPERATOR, Role.USER])
