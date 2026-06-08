"""
应用配置管理模块
使用pydantic-settings读取环境变量，支持.env文件加载
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置类"""

    # ========== 基础配置 ==========
    # 项目名称
    PROJECT_NAME: str = "FastAPI 后端服务"
    # 项目版本
    PROJECT_VERSION: str = "1.0.0"
    # API前缀
    API_PREFIX: str = "/api/v1"
    # 运行环境: development, testing, production
    ENV: str = "development"
    # 调试模式
    DEBUG: bool = False

    # ========== 服务配置 ==========
    # 服务主机
    HOST: str = "0.0.0.0"
    # 服务端口
    PORT: int = 8000
    # 允许的跨域源
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # ========== 数据库配置 ==========
    # PostgreSQL连接配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "fastapi_db"
    DATABASE_URL: Optional[str] = None
    # 数据库连接URL（自动构建）
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """构建异步数据库连接URL"""
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # 数据库连接池配置
    DB_POOL_SIZE: int = 20  # 连接池大小
    DB_MAX_OVERFLOW: int = 10  # 最大溢出连接数
    DB_POOL_TIMEOUT: int = 30  # 连接超时时间（秒）
    DB_POOL_RECYCLE: int = 3600  # 连接回收时间（秒）
    DB_ECHO: bool = False  # 是否打印SQL语句

    # ========== Redis配置 ==========
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    # Redis连接URL（自动构建）
    @property
    def REDIS_URL(self) -> str:
        """构建Redis连接URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Redis连接池配置
    REDIS_POOL_SIZE: int = 50  # 连接池大小
    REDIS_SOCKET_TIMEOUT: int = 5  # Socket超时时间（秒）
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5  # 连接超时时间（秒）

    # ========== JWT配置 ==========
    # JWT密钥（生产环境必须修改！）
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production-please-0123456789"
    # JWT算法
    JWT_ALGORITHM: str = "HS256"
    # Access Token过期时间（分钟）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Refresh Token过期时间（天）
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Token签发者
    JWT_ISSUER: str = "fastapi-backend"
    # Token接收者
    JWT_AUDIENCE: str = "fastapi-frontend"

    # ========== 退款规则配置 ==========
    # 允许退款的最大天数（订单完成后天数）
    REFUND_MAX_DAYS: int = 7
    # 全额退款阈值（小时，小于此时间全额退款）
    REFUND_FULL_REFUND_HOURS: int = 24
    # 退款手续费比例（如0.1表示10%手续费）
    REFUND_FEE_RATE: float = 0.1
    # 最低退款手续费金额
    REFUND_MIN_FEE: float = 1.0
    # 最高退款手续费金额（0表示不限制）
    REFUND_MAX_FEE: float = 100.0
    # 部分退款比例限制（如0.5表示最多退50%）
    REFUND_PARTIAL_MAX_RATE: float = 0.8

    # ========== 备份配置 ==========
    # 数据库备份是否启用
    BACKUP_ENABLED: bool = True
    # 备份保留天数
    BACKUP_RETENTION_DAYS: int = 30
    # 备份目录
    BACKUP_DIR: str = "/backup"
    # 备份时间（小时，0-23）- 每天凌晨2点
    BACKUP_HOUR: int = 2
    # 备份时间（分钟，0-59）
    BACKUP_MINUTE: int = 0
    # 是否压缩备份文件
    BACKUP_COMPRESS: bool = True
    # 备份文件名前缀
    BACKUP_PREFIX: str = "cat_hotel_db_backup"
    # 是否上传到S3兼容云存储
    BACKUP_UPLOAD_S3: bool = False
    # S3 兼容云存储端点
    BACKUP_S3_ENDPOINT: str = ""
    # S3 Bucket名称
    BACKUP_S3_BUCKET: str = ""
    # S3访问密钥
    BACKUP_S3_ACCESS_KEY: str = ""
    # S3秘密密钥
    BACKUP_S3_SECRET_KEY: str = ""
    # S3路径前缀
    BACKUP_S3_PREFIX: str = "backups/"

    # ========== 限流配置 ==========
    # 全局每秒请求数限制
    RATE_LIMIT_PER_SECOND: int = 100
    # 单个IP每分钟请求数限制
    RATE_LIMIT_PER_MINUTE: int = 1000
    # 限流时间窗口（秒）
    RATE_LIMIT_WINDOW: int = 60

    # ========== 日志配置 ==========
    # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL: str = "INFO"
    # 日志文件路径
    LOG_FILE_PATH: str = "/app/logs/app.log"
    # 日志文件最大大小（MB）
    LOG_MAX_BYTES: int = 10
    # 日志文件备份数量
    LOG_BACKUP_COUNT: int = 10
    # 是否输出到控制台
    LOG_CONSOLE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# 全局配置实例
settings = Settings()
