"""
数据库会话管理模块
提供SQLAlchemy异步连接、会话管理和连接池优化
"""
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.config.settings import settings


# 数据库模型基类
Base = declarative_base()


class DatabaseManager:
    """数据库管理器类，负责管理数据库连接和会话"""

    _instance: Optional["DatabaseManager"] = None
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    def __new__(cls) -> "DatabaseManager":
        """单例模式，确保只有一个数据库管理器实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        """获取数据库管理器单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def init_engine(self) -> None:
        """初始化数据库引擎和连接池"""
        if self._engine is not None:
            return

        # 创建异步数据库引擎，配置连接池优化
        self._engine = create_async_engine(
            settings.SQLALCHEMY_DATABASE_URI,
            # 连接池类：使用异步适配的队列连接池
            poolclass=AsyncAdaptedQueuePool,
            # 连接池大小：控制同时存在的连接数
            pool_size=settings.DB_POOL_SIZE,
            # 最大溢出连接数：允许超出pool_size的额外连接数
            max_overflow=settings.DB_MAX_OVERFLOW,
            # 连接超时时间：从连接池获取连接的最大等待时间
            pool_timeout=settings.DB_POOL_TIMEOUT,
            # 连接回收时间：防止连接被数据库服务器主动断开
            pool_recycle=settings.DB_POOL_RECYCLE,
            # 是否在每次连接取出时进行连接有效性检查
            pool_pre_ping=True,
            # 是否输出SQL语句（调试用）
            echo=settings.DB_ECHO,
            # 连接参数
            connect_args={
                "server_settings": {
                    "timezone": "Asia/Shanghai",
                    "application_name": settings.PROJECT_NAME
                }
            }
        )

        # 创建会话工厂
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            # 不自动提交，需要显式调用commit()
            autoflush=False,
            # 不自动提交事务
            autocommit=False,
            # 会话过期时不自动刷新对象
            expire_on_commit=False,
            # 异步会话类
            class_=AsyncSession
        )

    def get_engine(self) -> AsyncEngine:
        """获取数据库引擎实例"""
        if self._engine is None:
            self.init_engine()
        return self._engine

    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """获取会话工厂"""
        if self._session_factory is None:
            self.init_engine()
        return self._session_factory

    async def create_tables(self) -> None:
        """创建所有数据表（仅开发环境使用）"""
        engine = self.get_engine()
        async with engine.begin() as conn:
            # 使用metadata.create_all创建所有表
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """删除所有数据表（仅测试环境使用）"""
        engine = self.get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self) -> None:
        """关闭数据库连接，释放资源"""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


# 全局数据库管理器实例
db_manager = DatabaseManager.get_instance()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI依赖注入函数，用于获取数据库会话

    使用示例:
        @app.get("/items/")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    session_factory = db_manager.get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database() -> None:
    """初始化数据库连接和表结构（应用启动时调用）"""
    db_manager.init_engine()
    # 生产环境建议使用Alembic进行数据库迁移
    if settings.ENV == "development":
        await db_manager.create_tables()


async def close_database() -> None:
    """关闭数据库连接（应用关闭时调用）"""
    await db_manager.close()
