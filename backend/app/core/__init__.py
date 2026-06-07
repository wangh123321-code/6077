"""
核心模块
包含安全认证、异常处理、中间件等核心功能
"""
from app.core.security import (
    Role,
    TokenType,
    TokenPayload,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    RoleRequired,
    admin_required,
    operator_required,
    user_required
)
from app.core.errors import (
    ErrorCode,
    BusinessException,
    ParameterValidationException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
    RateLimitException,
    DatabaseException,
    RefundException,
    register_exception_handlers
)
from app.core.middleware import register_middlewares

__all__ = [
    # security
    "Role",
    "TokenType",
    "TokenPayload",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user",
    "RoleRequired",
    "admin_required",
    "operator_required",
    "user_required",
    # errors
    "ErrorCode",
    "BusinessException",
    "ParameterValidationException",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "ConflictException",
    "RateLimitException",
    "DatabaseException",
    "RefundException",
    "register_exception_handlers",
    # middleware
    "register_middlewares",
]
