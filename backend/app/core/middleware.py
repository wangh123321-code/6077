"""
中间件模块
提供请求ID、日志、限流、CORS等中间件
"""
import time
import uuid
import logging
from typing import Callable
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp

from app.config.settings import settings
from app.core.errors import ErrorCode, create_error_response


# ========== 请求ID中间件 ==========
class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    请求ID中间件
    为每个请求生成唯一的请求ID，用于链路追踪
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        中间件处理函数

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        # 生成请求ID，优先使用请求头中的X-Request-ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # 将请求ID存入request.state，供后续使用
        request.state.request_id = request_id
        # 存入请求状态，供日志使用
        request.state.start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 在响应头中添加请求ID
        response.headers["X-Request-ID"] = request_id
        # 添加处理时间
        process_time = (time.time() - request.state.start_time) * 1000
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        return response


# ========== 日志中间件 ==========
class LoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    记录每个请求的详细日志信息
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
        # 配置日志格式
        self._setup_logger()

    def _setup_logger(self) -> None:
        """配置日志"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(settings.LOG_LEVEL)

    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端真实IP

        Args:
            request: 请求对象

        Returns:
            客户端IP地址
        """
        # 优先从代理头获取真实IP
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip

        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        中间件处理函数

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        request_id = getattr(request.state, "request_id", "unknown")
        client_ip = self._get_client_ip(request)
        method = request.method
        path = request.url.path
        query_string = request.url.query
        user_agent = request.headers.get("User-Agent", "unknown")

        # 记录请求开始日志
        start_time = time.time()
        self.logger.info(
            f"[{request_id}] 请求开始 - IP: {client_ip}, Method: {method}, "
            f"Path: {path}, Query: {query_string}, UA: {user_agent}"
        )

        try:
            # 处理请求
            response = await call_next(request)

            # 计算处理时间
            process_time = (time.time() - start_time) * 1000
            status_code = response.status_code

            # 记录请求结束日志
            self.logger.info(
                f"[{request_id}] 请求完成 - Status: {status_code}, "
                f"Duration: {process_time:.2f}ms"
            )

            return response

        except Exception as e:
            # 记录异常日志
            process_time = (time.time() - start_time) * 1000
            self.logger.error(
                f"[{request_id}] 请求异常 - Error: {str(e)}, "
                f"Duration: {process_time:.2f}ms",
                exc_info=True
            )
            raise


# ========== 限流中间件 ==========
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    限流中间件
    基于IP的滑动窗口限流算法
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
        # 存储每个IP的请求时间戳列表
        self.ip_requests: dict[str, list[float]] = defaultdict(list)
        # 限流配置
        self.limit_per_minute = settings.RATE_LIMIT_PER_MINUTE
        self.window_seconds = settings.RATE_LIMIT_WINDOW

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        中间件处理函数

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        # 跳过一些不需要限流的路径
        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        if request.url.path in skip_paths:
            return await call_next(request)

        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        request_id = getattr(request.state, "request_id", "unknown")
        current_time = time.time()

        # 清理超出时间窗口的请求记录
        window_start = current_time - self.window_seconds
        self.ip_requests[client_ip] = [
            t for t in self.ip_requests[client_ip] if t > window_start
        ]

        # 检查是否超出限流
        if len(self.ip_requests[client_ip]) >= self.limit_per_minute:
            self.logger.warning(
                f"[{request_id}] 触发限流 - IP: {client_ip}, "
                f"Requests: {len(self.ip_requests[client_ip])}, "
                f"Limit: {self.limit_per_minute}/{self.window_seconds}s"
            )

            # 返回限流响应
            response_data = create_error_response(
                code=ErrorCode.TOO_MANY_REQUESTS,
                message="请求过于频繁，请稍后再试",
                data={
                    "limit": self.limit_per_minute,
                    "window": self.window_seconds,
                    "retry_after": max(0, int(window_start + self.window_seconds - current_time))
                },
                request_id=request_id
            )

            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=response_data
            )
            response.headers["Retry-After"] = str(
                max(0, int(window_start + self.window_seconds - current_time))
            )
            return response

        # 记录当前请求
        self.ip_requests[client_ip].append(current_time)

        # 定期清理过期的IP记录（防止内存泄漏）
        if len(self.ip_requests) > 10000:
            self._cleanup_expired_ips(current_time)

        return await call_next(request)

    def _cleanup_expired_ips(self, current_time: float) -> None:
        """
        清理过期的IP记录

        Args:
            current_time: 当前时间戳
        """
        window_start = current_time - self.window_seconds
        expired_ips = [
            ip for ip, times in self.ip_requests.items()
            if not times or times[-1] < window_start
        ]
        for ip in expired_ips:
            del self.ip_requests[ip]


# ========== 安全头中间件 ==========
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全头中间件
    添加安全相关的HTTP响应头
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        中间件处理函数

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        response = await call_next(request)

        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:;"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response


# ========== 统一响应格式中间件 ==========
class ResponseFormatMiddleware(BaseHTTPMiddleware):
    """
    统一响应格式中间件
    将成功响应包装成统一格式
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        中间件处理函数

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        # 跳过OpenAPI相关路径
        skip_paths = ["/openapi.json", "/docs", "/redoc", "/health"]
        if request.url.path in skip_paths:
            return await call_next(request)

        response = await call_next(request)

        # 只对JSON响应进行包装
        if (
            isinstance(response, JSONResponse)
            and response.status_code < 400
        ):
            request_id = getattr(request.state, "request_id", "")
            original_body = response.body

            try:
                import json
                original_data = json.loads(original_body)

                # 如果已经是标准格式，则不进行包装
                if isinstance(original_data, dict) and "code" in original_data:
                    return response

                # 包装成统一格式
                formatted_data = {
                    "code": ErrorCode.SUCCESS,
                    "message": "success",
                    "data": original_data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": request_id
                }

                return JSONResponse(
                    content=formatted_data,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            except Exception:
                # 如果解析失败，返回原始响应
                return response

        return response


# ========== 注册中间件 ==========
def register_middlewares(app) -> None:
    """
    向FastAPI应用注册所有中间件

    注意：中间件的注册顺序很重要，先注册的中间件会先处理请求，后处理响应
    执行顺序:
    请求 -> RequestId -> SecurityHeaders -> Logging -> RateLimit -> CORS -> ResponseFormat -> 路由

    Args:
        app: FastAPI应用实例
    """
    # 1. 请求ID中间件（最先注册，确保所有后续中间件都能获取到request_id）
    app.add_middleware(RequestIdMiddleware)

    # 2. 安全头中间件
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. 日志中间件
    app.add_middleware(LoggingMiddleware)

    # 4. 限流中间件
    app.add_middleware(RateLimitMiddleware)

    # 5. CORS中间件（使用Starlette内置的CORSMiddleware）
    app.add_middleware(
        CORSMiddleware,
        # 允许的源列表
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        # 允许携带凭证（Cookie等）
        allow_credentials=True,
        # 允许的HTTP方法
        allow_methods=["*"],
        # 允许的请求头
        allow_headers=["*"],
        # 预检请求的缓存时间（秒）
        max_age=600,
        # 暴露给前端的响应头
        expose_headers=["X-Request-ID", "X-Process-Time"]
    )

    # 6. 统一响应格式中间件
    app.add_middleware(ResponseFormatMiddleware)
