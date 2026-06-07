"""
异常处理模块
提供自定义异常类和全局异常处理器
"""
from typing import Any, Optional, Union
from datetime import datetime

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from pydantic import ValidationError

from app.config.settings import settings


# ========== 业务错误码定义 ==========
class ErrorCode:
    """业务错误码常量类"""

    # ========== 通用错误 (1000-1999) ==========
    SUCCESS = 0  # 成功
    UNKNOWN_ERROR = 1000  # 未知错误
    INVALID_PARAMETER = 1001  # 参数错误
    UNAUTHORIZED = 1002  # 未授权
    FORBIDDEN = 1003  # 权限不足
    NOT_FOUND = 1004  # 资源不存在
    METHOD_NOT_ALLOWED = 1005  # 方法不允许
    CONFLICT = 1006  # 资源冲突
    TOO_MANY_REQUESTS = 1007  # 请求过于频繁
    SERVICE_UNAVAILABLE = 1008  # 服务不可用
    TIMEOUT = 1009  # 请求超时

    # ========== 认证错误 (2000-2099) ==========
    INVALID_TOKEN = 2001  # Token无效
    TOKEN_EXPIRED = 2002  # Token已过期
    TOKEN_TYPE_ERROR = 2003  # Token类型错误
    INVALID_CREDENTIALS = 2004  # 用户名或密码错误
    ACCOUNT_DISABLED = 2005  # 账号已禁用
    ACCOUNT_LOCKED = 2006  # 账号已锁定
    REFRESH_TOKEN_INVALID = 2007  # Refresh Token无效
    REFRESH_TOKEN_EXPIRED = 2008  # Refresh Token已过期

    # ========== 用户错误 (2100-2199) ==========
    USER_NOT_FOUND = 2101  # 用户不存在
    USER_ALREADY_EXISTS = 2102  # 用户已存在
    INVALID_PASSWORD = 2103  # 密码错误
    PASSWORD_TOO_WEAK = 2104  # 密码强度不足
    EMAIL_ALREADY_EXISTS = 2105  # 邮箱已存在
    PHONE_ALREADY_EXISTS = 2106  # 手机号已存在

    # ========== 数据库错误 (3000-3099) ==========
    DATABASE_ERROR = 3001  # 数据库错误
    DATABASE_CONNECTION_ERROR = 3002  # 数据库连接错误
    DATABASE_INTEGRITY_ERROR = 3003  # 数据完整性错误
    RECORD_NOT_FOUND = 3004  # 记录不存在
    RECORD_ALREADY_EXISTS = 3005  # 记录已存在

    # ========== 业务错误 (4000-4999) ==========
    REFUND_NOT_ALLOWED = 4001  # 不允许退款
    REFUND_AMOUNT_EXCEEDED = 4002  # 退款金额超限
    REFUND_TIME_EXPIRED = 4003  # 退款时间已过
    ORDER_NOT_FOUND = 4004  # 订单不存在
    ORDER_STATUS_ERROR = 4005  # 订单状态错误
    INSUFFICIENT_BALANCE = 4006  # 余额不足

    # ========== 系统错误 (5000-5999) ==========
    REDIS_CONNECTION_ERROR = 5001  # Redis连接错误
    REDIS_LOCK_ERROR = 5002  # Redis锁错误
    FILE_UPLOAD_ERROR = 5101  # 文件上传错误
    FILE_TOO_LARGE = 5102  # 文件过大
    FILE_TYPE_NOT_ALLOWED = 5103  # 文件类型不允许


# ========== 自定义异常基类 ==========
class BusinessException(Exception):
    """业务异常基类"""

    def __init__(
        self,
        code: int = ErrorCode.UNKNOWN_ERROR,
        message: str = "服务器内部错误",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        data: Optional[Any] = None
    ):
        """
        初始化业务异常

        Args:
            code: 业务错误码
            message: 错误消息
            status_code: HTTP状态码
            data: 附加数据
        """
        self.code = code
        self.message = message
        self.status_code = status_code
        self.data = data
        super().__init__(message)

    def __str__(self) -> str:
        return f"[Code: {self.code}] {self.message}"

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data,
            "timestamp": datetime.now().isoformat(),
            "request_id": ""  # 由中间件填充
        }


# ========== 参数验证异常 ==========
class ParameterValidationException(BusinessException):
    """参数验证异常"""

    def __init__(self, message: str = "参数验证失败", data: Optional[Any] = None):
        super().__init__(
            code=ErrorCode.INVALID_PARAMETER,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=data
        )


# ========== 未授权异常 ==========
class UnauthorizedException(BusinessException):
    """未授权异常"""

    def __init__(self, message: str = "未授权访问", code: int = ErrorCode.UNAUTHORIZED):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


# ========== 权限不足异常 ==========
class ForbiddenException(BusinessException):
    """权限不足异常"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(
            code=ErrorCode.FORBIDDEN,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


# ========== 资源不存在异常 ==========
class NotFoundException(BusinessException):
    """资源不存在异常"""

    def __init__(self, message: str = "资源不存在", code: int = ErrorCode.NOT_FOUND):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )


# ========== 资源冲突异常 ==========
class ConflictException(BusinessException):
    """资源冲突异常"""

    def __init__(self, message: str = "资源冲突", code: int = ErrorCode.CONFLICT, data: Optional[Any] = None):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            data=data
        )


# ========== 请求过于频繁异常 ==========
class RateLimitException(BusinessException):
    """请求限流异常"""

    def __init__(self, message: str = "请求过于频繁，请稍后再试"):
        super().__init__(
            code=ErrorCode.TOO_MANY_REQUESTS,
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


# ========== 数据库异常 ==========
class DatabaseException(BusinessException):
    """数据库异常"""

    def __init__(
        self,
        message: str = "数据库操作失败",
        code: int = ErrorCode.DATABASE_ERROR,
        data: Optional[Any] = None
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=data
        )


# ========== 退款异常 ==========
class RefundException(BusinessException):
    """退款异常"""

    def __init__(self, message: str = "退款失败", code: int = ErrorCode.REFUND_NOT_ALLOWED):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


# ========== 统一响应格式 ==========
def create_error_response(
    code: int,
    message: str,
    data: Optional[Any] = None,
    request_id: str = ""
) -> dict:
    """
    创建统一格式的错误响应

    Args:
        code: 错误码
        message: 错误消息
        data: 附加数据
        request_id: 请求ID

    Returns:
        统一格式的响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id
    }


# ========== 全局异常处理器 ==========
async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """
    处理业务异常

    Args:
        request: 请求对象
        exc: 业务异常对象

    Returns:
        JSON响应
    """
    request_id = getattr(request.state, "request_id", "")
    response_data = create_error_response(
        code=exc.code,
        message=exc.message,
        data=exc.data,
        request_id=request_id
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求参数验证异常

    Args:
        request: 请求对象
        exc: 参数验证异常对象

    Returns:
        JSON响应
    """
    request_id = getattr(request.state, "request_id", "")

    # 格式化验证错误信息
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")

    error_message = "; ".join(errors) if errors else "参数验证失败"

    response_data = create_error_response(
        code=ErrorCode.INVALID_PARAMETER,
        message=error_message,
        data=[{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()],
        request_id=request_id
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response_data
    )


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    处理Pydantic模型验证异常

    Args:
        request: 请求对象
        exc: Pydantic验证异常对象

    Returns:
        JSON响应
    """
    request_id = getattr(request.state, "request_id", "")

    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")

    error_message = "; ".join(errors) if errors else "数据验证失败"

    response_data = create_error_response(
        code=ErrorCode.INVALID_PARAMETER,
        message=error_message,
        data=exc.errors(),
        request_id=request_id
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response_data
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    处理SQLAlchemy数据库异常

    Args:
        request: 请求对象
        exc: SQLAlchemy异常对象

    Returns:
        JSON响应
    """
    request_id = getattr(request.state, "request_id", "")

    if isinstance(exc, IntegrityError):
        error_code = ErrorCode.DATABASE_INTEGRITY_ERROR
        message = "数据完整性错误，可能违反了唯一约束或外键约束"
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, OperationalError):
        error_code = ErrorCode.DATABASE_CONNECTION_ERROR
        message = "数据库连接错误"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        error_code = ErrorCode.DATABASE_ERROR
        message = "数据库操作失败"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    # 生产环境不暴露详细数据库错误信息
    detail = str(exc) if settings.DEBUG else None

    response_data = create_error_response(
        code=error_code,
        message=message,
        data=detail,
        request_id=request_id
    )
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理HTTP异常

    Args:
        request: 请求对象
        exc: HTTP异常对象

    Returns:
        JSON响应
    """
    from fastapi import HTTPException

    request_id = getattr(request.state, "request_id", "")

    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        detail = exc.detail

        # 映射HTTP状态码到业务错误码
        if status_code == status.HTTP_401_UNAUTHORIZED:
            code = ErrorCode.UNAUTHORIZED
            message = detail or "未授权访问"
        elif status_code == status.HTTP_403_FORBIDDEN:
            code = ErrorCode.FORBIDDEN
            message = detail or "权限不足"
        elif status_code == status.HTTP_404_NOT_FOUND:
            code = ErrorCode.NOT_FOUND
            message = detail or "资源不存在"
        elif status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            code = ErrorCode.METHOD_NOT_ALLOWED
            message = detail or "方法不允许"
        elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            code = ErrorCode.TOO_MANY_REQUESTS
            message = detail or "请求过于频繁"
        else:
            code = ErrorCode.UNKNOWN_ERROR
            message = detail or "请求处理失败"
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        code = ErrorCode.UNKNOWN_ERROR
        message = "服务器内部错误" if not settings.DEBUG else str(exc)

    response_data = create_error_response(
        code=code,
        message=message,
        data=str(exc) if settings.DEBUG else None,
        request_id=request_id
    )
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理所有其他未捕获的异常

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSON响应
    """
    import logging
    logger = logging.getLogger(__name__)
    request_id = getattr(request.state, "request_id", "")

    # 记录异常日志
    logger.error(f"未捕获的异常 [RequestID: {request_id}]: {str(exc)}", exc_info=True)

    # 生产环境隐藏详细错误信息
    message = "服务器内部错误" if not settings.DEBUG else str(exc)

    response_data = create_error_response(
        code=ErrorCode.UNKNOWN_ERROR,
        message=message,
        data=str(exc) if settings.DEBUG else None,
        request_id=request_id
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


# ========== 注册全局异常处理器 ==========
def register_exception_handlers(app):
    """
    向FastAPI应用注册所有全局异常处理器

    Args:
        app: FastAPI应用实例
    """
    from fastapi import HTTPException
    from fastapi.exceptions import RequestValidationError

    # 注册业务异常处理器
    app.add_exception_handler(BusinessException, business_exception_handler)
    # 注册请求参数验证异常处理器
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    # 注册Pydantic验证异常处理器
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    # 注册SQLAlchemy异常处理器
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    # 注册HTTP异常处理器
    app.add_exception_handler(HTTPException, http_exception_handler)
    # 注册通用异常处理器（必须放在最后）
    app.add_exception_handler(Exception, general_exception_handler)
