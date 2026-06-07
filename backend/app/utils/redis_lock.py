"""
Redis分布式锁模块
提供基于Redis的分布式锁实现，支持异步操作
"""
import asyncio
import uuid
import logging
from typing import Optional, Any
from contextlib import asynccontextmanager

import redis.asyncio as redis_async

from app.config.settings import settings
from app.core.errors import DatabaseException, ErrorCode


logger = logging.getLogger(__name__)


# ========== Redis连接管理器 ==========
class RedisManager:
    """Redis连接管理器，负责管理Redis连接和连接池"""

    _instance: Optional["RedisManager"] = None
    _client: Optional[redis_async.Redis] = None

    def __new__(cls) -> "RedisManager":
        """单例模式，确保只有一个Redis管理器实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "RedisManager":
        """获取Redis管理器单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def init_client(self) -> None:
        """初始化Redis客户端和连接池"""
        if self._client is not None and not self._client.connection_pool.connection_kwargs.get("disconnected", False):
            return

        try:
            # 创建异步Redis客户端，配置连接池
            self._client = redis_async.Redis.from_url(
                settings.REDIS_URL,
                # 连接池大小
                max_connections=settings.REDIS_POOL_SIZE,
                # Socket读取超时时间
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                # Socket连接超时时间
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                # 连接池是否阻塞等待
                pool_block=True,
                # 连接池最大等待时间（毫秒）
                pool_timeout=5000,
                # 编码
                encoding="utf-8",
                # 自动解码响应
                decode_responses=True,
                # 健康检查间隔（秒）
                health_check_interval=30,
                # 重试次数
                retry_on_timeout=3
            )

            # 测试连接
            await self._client.ping()
            logger.info("Redis连接初始化成功")

        except Exception as e:
            logger.error(f"Redis连接初始化失败: {str(e)}", exc_info=True)
            raise DatabaseException(
                code=ErrorCode.REDIS_CONNECTION_ERROR,
                message="Redis连接失败"
            )

    async def get_client(self) -> redis_async.Redis:
        """获取Redis客户端实例"""
        if self._client is None:
            await self.init_client()
        return self._client

    async def close(self) -> None:
        """关闭Redis连接，释放资源"""
        if self._client is not None:
            await self._client.close()
            self._client = None
            logger.info("Redis连接已关闭")


# 全局Redis管理器实例
redis_manager = RedisManager.get_instance()


# ========== 分布式锁实现 ==========
class RedisDistributedLock:
    """
    基于Redis的分布式锁实现

    使用Redis的SETNX + Lua脚本实现原子性的加锁和解锁操作，
    确保分布式环境下的互斥性和安全性。

    主要特性：
    1. 支持锁超时，自动释放，防止死锁
    2. 支持可重入锁（同一协程可重复获取）
    3. 使用Lua脚本保证解锁的原子性
    4. 支持阻塞等待获取锁
    """

    # 锁的键前缀
    LOCK_KEY_PREFIX = "lock:"
    # 锁的默认超时时间（秒）
    DEFAULT_LOCK_TIMEOUT = 30
    # 默认重试间隔（毫秒）
    DEFAULT_RETRY_INTERVAL = 100
    # 默认最大重试次数
    DEFAULT_MAX_RETRIES = 30

    def __init__(
        self,
        lock_name: str,
        lock_timeout: int = DEFAULT_LOCK_TIMEOUT,
        retry_interval: int = DEFAULT_RETRY_INTERVAL,
        max_retries: int = DEFAULT_MAX_RETRIES
    ):
        """
        初始化分布式锁

        Args:
            lock_name: 锁的名称（全局唯一）
            lock_timeout: 锁的超时时间（秒），超时后自动释放
            retry_interval: 获取锁失败后的重试间隔（毫秒）
            max_retries: 最大重试次数
        """
        self.lock_name = lock_name
        self.lock_key = f"{self.LOCK_KEY_PREFIX}{lock_name}"
        self.lock_timeout = lock_timeout
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        # 锁的唯一标识，用于安全解锁
        self._lock_value: Optional[str] = None
        # 重入计数
        self._reentrant_count: int = 0
        # 当前协程ID，用于可重入判断
        self._owner_task_id: Optional[int] = None

    @property
    def is_locked(self) -> bool:
        """检查锁是否被当前实例持有"""
        return self._lock_value is not None and self._reentrant_count > 0

    async def acquire(self, blocking: bool = True) -> bool:
        """
        获取锁

        Args:
            blocking: 是否阻塞等待获取锁

        Returns:
            True表示获取成功，False表示获取失败

        Raises:
            DatabaseException: Redis连接错误时抛出
        """
        try:
            client = await redis_manager.get_client()
        except Exception as e:
            logger.error(f"获取Redis客户端失败: {str(e)}")
            raise DatabaseException(
                code=ErrorCode.REDIS_CONNECTION_ERROR,
                message="Redis连接失败"
            )

        current_task_id = id(asyncio.current_task())

        # 检查是否是重入锁
        if self.is_locked and self._owner_task_id == current_task_id:
            self._reentrant_count += 1
            logger.debug(f"重入锁 {self.lock_name}, 当前重入次数: {self._reentrant_count}")
            return True

        # 生成唯一的锁值
        lock_value = f"{uuid.uuid4().hex}:{current_task_id}"
        retries = 0

        while True:
            try:
                # 使用SET命令原子性地获取锁
                # NX: 只有键不存在时才设置
                # PX: 设置过期时间（毫秒）
                result = await client.set(
                    self.lock_key,
                    lock_value,
                    nx=True,
                    px=self.lock_timeout * 1000
                )

                if result:
                    # 获取锁成功
                    self._lock_value = lock_value
                    self._reentrant_count = 1
                    self._owner_task_id = current_task_id
                    logger.debug(f"成功获取锁 {self.lock_name}")
                    return True

                if not blocking:
                    # 非阻塞模式，直接返回失败
                    return False

                # 检查是否超过最大重试次数
                retries += 1
                if retries >= self.max_retries:
                    logger.warning(f"获取锁 {self.lock_name} 超时，已重试 {retries} 次")
                    return False

                # 等待后重试
                await asyncio.sleep(self.retry_interval / 1000)

            except Exception as e:
                logger.error(f"获取锁 {self.lock_name} 时发生异常: {str(e)}", exc_info=True)
                raise DatabaseException(
                    code=ErrorCode.REDIS_LOCK_ERROR,
                    message=f"获取锁失败: {str(e)}"
                )

    async def release(self) -> bool:
        """
        释放锁

        使用Lua脚本确保解锁的原子性，避免误删其他客户端持有的锁。

        Returns:
            True表示释放成功，False表示释放失败

        Raises:
            DatabaseException: Redis连接错误或非锁持有者尝试解锁时抛出
        """
        if not self.is_locked:
            logger.warning(f"尝试释放未持有的锁 {self.lock_name}")
            return False

        current_task_id = id(asyncio.current_task())
        if self._owner_task_id != current_task_id:
            logger.warning(f"非锁持有者尝试释放锁 {self.lock_name}")
            raise DatabaseException(
                code=ErrorCode.REDIS_LOCK_ERROR,
                message="非锁持有者无法释放锁"
            )

        # 处理重入锁
        self._reentrant_count -= 1
        if self._reentrant_count > 0:
            logger.debug(f"锁 {self.lock_name} 重入次数减1，剩余: {self._reentrant_count}")
            return True

        try:
            client = await redis_manager.get_client()

            # 使用Lua脚本原子性地检查并删除锁
            # 脚本逻辑：如果键存在且值匹配，则删除，否则返回0
            unlock_script = """
                if redis.call('get', KEYS[1]) == ARGV[1] then
                    return redis.call('del', KEYS[1])
                else
                    return 0
                end
            """

            result = await client.eval(
                unlock_script,
                1,  # KEYS的数量
                self.lock_key,  # KEYS[1]
                self._lock_value  # ARGV[1]
            )

            if result == 1:
                logger.debug(f"成功释放锁 {self.lock_name}")
                self._lock_value = None
                self._owner_task_id = None
                self._reentrant_count = 0
                return True
            else:
                logger.warning(f"释放锁 {self.lock_name} 失败，锁可能已过期或被其他进程持有")
                self._lock_value = None
                self._owner_task_id = None
                self._reentrant_count = 0
                return False

        except Exception as e:
            logger.error(f"释放锁 {self.lock_name} 时发生异常: {str(e)}", exc_info=True)
            # 即使异常也重置锁状态，避免状态不一致
            self._lock_value = None
            self._owner_task_id = None
            self._reentrant_count = 0
            raise DatabaseException(
                code=ErrorCode.REDIS_LOCK_ERROR,
                message=f"释放锁失败: {str(e)}"
            )

    async def extend(self, additional_seconds: int) -> bool:
        """
        延长锁的过期时间

        Args:
            additional_seconds: 需要延长的额外秒数

        Returns:
            True表示延长成功，False表示延长失败
        """
        if not self.is_locked:
            logger.warning(f"尝试延长未持有的锁 {self.lock_name}")
            return False

        current_task_id = id(asyncio.current_task())
        if self._owner_task_id != current_task_id:
            logger.warning(f"非锁持有者尝试延长锁 {self.lock_name}")
            return False

        try:
            client = await redis_manager.get_client()

            # 使用Lua脚本原子性地延长锁
            extend_script = """
                if redis.call('get', KEYS[1]) == ARGV[1] then
                    return redis.call('pexpire', KEYS[1], ARGV[2])
                else
                    return 0
                end
            """

            result = await client.eval(
                extend_script,
                1,
                self.lock_key,
                self._lock_value,
                (self.lock_timeout + additional_seconds) * 1000
            )

            if result == 1:
                logger.debug(f"成功延长锁 {self.lock_name} 过期时间 {additional_seconds} 秒")
                self.lock_timeout += additional_seconds
                return True
            else:
                logger.warning(f"延长锁 {self.lock_name} 过期时间失败")
                return False

        except Exception as e:
            logger.error(f"延长锁 {self.lock_name} 时发生异常: {str(e)}", exc_info=True)
            raise DatabaseException(
                code=ErrorCode.REDIS_LOCK_ERROR,
                message=f"延长锁失败: {str(e)}"
            )

    async def __aenter__(self) -> "RedisDistributedLock":
        """异步上下文管理器入口"""
        await self.acquire(blocking=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.release()


# ========== 便捷函数 ==========
@asynccontextmanager
async def redis_lock(
    lock_name: str,
    lock_timeout: int = RedisDistributedLock.DEFAULT_LOCK_TIMEOUT,
    blocking: bool = True,
    retry_interval: int = RedisDistributedLock.DEFAULT_RETRY_INTERVAL,
    max_retries: int = RedisDistributedLock.DEFAULT_MAX_RETRIES
):
    """
    获取Redis分布式锁的便捷异步上下文管理器

    使用示例:
        async with redis_lock("order_process_123"):
            # 需要互斥执行的代码
            process_order()

    Args:
        lock_name: 锁的名称（全局唯一）
        lock_timeout: 锁的超时时间（秒）
        blocking: 是否阻塞等待获取锁
        retry_interval: 重试间隔（毫秒）
        max_retries: 最大重试次数

    Yields:
        RedisDistributedLock实例

    Raises:
        DatabaseException: 获取锁失败时抛出
    """
    lock = RedisDistributedLock(
        lock_name=lock_name,
        lock_timeout=lock_timeout,
        retry_interval=retry_interval,
        max_retries=max_retries
    )

    acquired = await lock.acquire(blocking=blocking)
    if not acquired:
        raise DatabaseException(
            code=ErrorCode.REDIS_LOCK_ERROR,
            message=f"获取锁 {lock_name} 失败"
        )

    try:
        yield lock
    finally:
        await lock.release()


# ========== Redis工具函数 ==========
async def get_redis_client() -> redis_async.Redis:
    """
    获取Redis客户端（依赖注入用）

    Returns:
        Redis异步客户端实例
    """
    return await redis_manager.get_client()


async def init_redis() -> None:
    """初始化Redis连接（应用启动时调用）"""
    await redis_manager.init_client()


async def close_redis() -> None:
    """关闭Redis连接（应用关闭时调用）"""
    await redis_manager.close()
