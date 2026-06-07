"""
FastAPI应用入口模块
初始化FastAPI应用，注册路由、中间件、异常处理器和启动/关闭事件
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.openapi.utils import get_openapi
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config.settings import settings
from app.core.middleware import register_middlewares
from app.core.errors import register_exception_handlers, ErrorCode
from app.database.session import init_database, close_database
from app.utils.redis_lock import init_redis, close_redis
from app.utils.backup import backup_service


# ========== 日志配置 ==========
def setup_logging() -> None:
    """配置应用日志"""
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(process)d - %(thread)d - %(message)s"
    )

    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
        ]
    )

    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DB_ECHO else logging.WARNING
    )


scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def scheduled_backup():
    """定时执行数据库备份任务"""
    logger = logging.getLogger(__name__)
    logger.info("开始执行定时数据库备份...")
    try:
        result = await backup_service.create_backup()
        logger.info(f"定时备份完成: {result['filename']}, 大小: {result['size_mb']}MB")
    except Exception as e:
        logger.error(f"定时备份失败: {str(e)}", exc_info=True)


# ========== 应用生命周期管理 ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    处理应用启动和关闭时的资源初始化与清理

    Args:
        app: FastAPI应用实例
    """
    # ========== 启动事件 ==========
    logger = logging.getLogger(__name__)
    logger.info(f"正在启动 {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}...")

    # 初始化数据库连接
    logger.info("正在初始化数据库连接...")
    await init_database()
    logger.info("数据库连接初始化完成")

    # 初始化Redis连接
    try:
        logger.info("正在初始化Redis连接...")
        await init_redis()
        logger.info("Redis连接初始化完成")
    except Exception as e:
        logger.warning(f"Redis连接初始化失败，部分功能可能不可用: {str(e)}")

    # 启动定时备份任务
    if settings.BACKUP_ENABLED:
        logger.info(
            f"正在启动定时备份任务，每天 {settings.BACKUP_HOUR:02d}:{settings.BACKUP_MINUTE:02d} 执行"
        )
        scheduler.add_job(
            scheduled_backup,
            "cron",
            hour=settings.BACKUP_HOUR,
            minute=settings.BACKUP_MINUTE,
            id="daily_backup",
            replace_existing=True
        )
        scheduler.start()
        logger.info("定时备份任务已启动")

    logger.info(f"{settings.PROJECT_NAME} 启动成功，运行环境: {settings.ENV}")

    yield

    # ========== 关闭事件 ==========
    logger.info("正在关闭应用...")

    # 关闭定时任务调度器
    if settings.BACKUP_ENABLED and scheduler.running:
        logger.info("正在关闭定时备份调度器...")
        scheduler.shutdown()
        logger.info("定时备份调度器已关闭")

    # 关闭数据库连接
    logger.info("正在关闭数据库连接...")
    await close_database()
    logger.info("数据库连接已关闭")

    # 关闭Redis连接
    logger.info("正在关闭Redis连接...")
    await close_redis()
    logger.info("Redis连接已关闭")

    logger.info("应用已成功关闭")


# ========== 自定义OpenAPI文档 ==========
def custom_openapi(app: FastAPI):
    """自定义OpenAPI文档配置"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=f"""
        # {settings.PROJECT_NAME} API文档

        ## 认证说明

        本API使用JWT令牌进行认证，认证流程如下：

        1. 调用登录接口获取Access Token和Refresh Token
        2. 在请求头中添加 `Authorization: Bearer <Access Token>`
        3. Access Token过期后，使用Refresh Token获取新的Access Token

        ## 错误码说明

        | 错误码 | 说明 |
        |--------|------|
        | 0 | 成功 |
        | 1000 | 未知错误 |
        | 1001 | 参数错误 |
        | 1002 | 未授权 |
        | 1003 | 权限不足 |
        | 1004 | 资源不存在 |
        | 1007 | 请求过于频繁 |

        ## 响应格式

        所有接口响应统一格式：
        ```json
        {{
            "code": 0,
            "message": "success",
            "data": {{}},
            "timestamp": "2024-01-01T00:00:00Z",
            "request_id": "uuid"
        }}
        ```
        """,
        routes=app.routes,
    )

    # 添加安全认证方案
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT认证，格式: Bearer <token>"
        }
    }

    # 全局安全要求
    openapi_schema["security"] = [{"BearerAuth": []}]

    # 服务器配置
    openapi_schema["servers"] = [
        {
            "url": "/",
            "description": "当前服务器"
        },
        {
            "url": "http://localhost:8000",
            "description": "开发服务器"
        }
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# ========== 创建FastAPI应用 ==========
def create_app() -> FastAPI:
    """
    创建并配置FastAPI应用实例

    Returns:
        配置完成的FastAPI应用实例
    """
    # 配置日志
    setup_logging()

    # 创建FastAPI应用
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=f"{settings.PROJECT_NAME} API服务",
        # 调试模式
        debug=settings.DEBUG,
        # 文档URL
        docs_url="/docs" if not settings.ENV == "production" else None,
        redoc_url="/redoc" if not settings.ENV == "production" else None,
        openapi_url="/openapi.json" if not settings.ENV == "production" else None,
        # 生命周期管理
        lifespan=lifespan,
        # 响应类型
        default_response_class=None,
    )

    # 生产环境启用HTTPS重定向
    if settings.ENV == "production":
        app.add_middleware(HTTPSRedirectMiddleware)

    # 注册中间件
    register_middlewares(app)

    # 注册异常处理器
    register_exception_handlers(app)

    # 注册路由
    register_routers(app)

    # 自定义OpenAPI文档
    app.openapi = lambda: custom_openapi(app)

    # 注册健康检查接口
    register_health_check(app)

    return app


# ========== 注册路由 ==========
def register_routers(app: FastAPI) -> None:
    """
    注册所有API路由

    Args:
        app: FastAPI应用实例
    """
    from app.api.v1 import api_router as v1_router

    app.include_router(v1_router, prefix=settings.API_PREFIX)


# ========== 健康检查接口 ==========
def register_health_check(app: FastAPI) -> None:
    """
    注册健康检查接口

    Args:
        app: FastAPI应用实例
    """
    from app.database.session import db_manager
    from app.utils.redis_lock import redis_manager

    @app.get("/health", summary="健康检查", tags=["系统"])
    async def health_check():
        """
        服务健康检查接口

        检查数据库、Redis等依赖服务的连接状态

        Returns:
            健康状态信息
        """
        import time

        status_result = {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.PROJECT_VERSION,
            "env": settings.ENV,
            "timestamp": time.time(),
            "checks": {}
        }

        # 检查数据库连接
        try:
            engine = db_manager.get_engine()
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
            status_result["checks"]["database"] = "healthy"
        except Exception as e:
            status_result["checks"]["database"] = f"unhealthy: {str(e)}"
            status_result["status"] = "unhealthy"

        # 检查Redis连接
        try:
            redis_client = await redis_manager.get_client()
            await redis_client.ping()
            status_result["checks"]["redis"] = "healthy"
        except Exception as e:
            status_result["checks"]["redis"] = f"unhealthy: {str(e)}"
            # Redis不健康不影响整体服务状态，标记为degraded
            if status_result["status"] == "healthy":
                status_result["status"] = "degraded"

        return status_result

    @app.get("/", summary="根路径", include_in_schema=False)
    async def root():
        """根路径重定向到API文档"""
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/docs")


# ========== 创建应用实例 ==========
# 全局应用实例，供uvicorn启动使用
app = create_app()


# ========== 启动应用 ==========
if __name__ == "__main__":
    """直接运行此文件启动应用"""
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG,
    )
