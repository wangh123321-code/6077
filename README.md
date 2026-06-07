# 猫咪民宿预订管理系统

杭州网红猫咪民宿完整预订管理系统，从线上预订、入住管理到服务结算全流程数字化。

## 技术栈

### 后端
- **FastAPI** - 高性能异步Web框架
- **PostgreSQL** - 关系型数据库
- **SQLAlchemy 2.0** - ORM框架（异步）
- **Redis** - 缓存和分布式锁
- **APScheduler** - 定时任务（数据备份）
- **JWT** - 身份认证

### 前端
- **Vue 3** - 渐进式JavaScript框架
- **TypeScript** - 类型安全
- **Pinia** - 状态管理
- **Vue Router 4** - 路由管理
- **Element Plus** - UI组件库
- **Vite** - 构建工具

### 运维
- **Docker** - 容器化部署
- **Docker Compose** - 编排工具
- **Nginx** - 反向代理和负载均衡
- **Gunicorn + Uvicorn** - ASGI服务器

## 核心功能

### 1. 在线预订模块
- 按日期筛选可用猫屋
- 查看猫屋实拍照片、设施配置、价格
- 在线支付完成预订
- 唯一核销码生成（二维码）
- 扫码核销入住

### 2. 猫屋管理模块
- 20间猫屋管理（名称、描述、价格、设施、图片）
- 状态管理（可用、已占用、维护中、清洁中）
- 按日期查询可用性

### 3. 服务套餐模块
- 基础服务（日常喂养、铲屎等）
- 增值服务（喂药、洗澡、撸猫陪玩等）
- 入住期间加购服务
- 自动记录服务时间和执行人

### 4. 会员体系模块
- 会员等级管理
- 积分系统（消费1元=1积分）
- 余额充值
- 积分兑换

## 并发控制（防超订）

**三重锁机制**确保同一猫屋同一时间段只能有一笔有效预订：

1. **Redis分布式锁**（第一层）
   - 锁键：`booking:{cat_room_id}:{check_in}:{check_out}`
   - 锁超时：30秒
   - 防止同一猫屋同一时间段的并发预订

2. **数据库乐观锁**（第二层）
   - 使用 `version` 字段
   - SQLAlchemy自动版本检查
   - 更新失败自动重试

3. **数据库唯一约束**（最后防线）
   - `(cat_room_id, check_in_date, check_out_date)` 联合唯一约束
   - 状态过滤：`status NOT IN ('cancelled', 'refunded')`
   - 捕获 `IntegrityError` 异常

## 退款规则（可配置）

通过环境变量配置退款规则：

- **提前 >= 7天** 取消：全额退款
- **提前 3-7天** 取消：退还 80%
- **提前 < 3天** 取消：不退款
- **已入住/已退房**：不允许退款

## 数据备份

- 每天凌晨2点自动全量备份
- 支持gzip压缩
- 自动清理超过30天的备份
- 支持上传到S3兼容云存储
- 支持从备份恢复

## 性能指标

- 支持 **500QPS** 预订请求
- Nginx限流配置：`burst=500 nodelay`
- 数据库连接池：20个连接
- Redis连接池：50个连接
- Gunicorn 4 worker进程

## 快速开始

### 一键启动（推荐）

```bash
# Windows
start.bat

# Linux/Mac
docker-compose up -d --build
```

### 服务地址

- 前端：http://localhost
- 后端API：http://localhost/api/v1
- API文档：http://localhost/docs
- 数据库：localhost:5432
- Redis：localhost:6379

### 初始化测试数据

```bash
cd backend
python scripts/init_test_data.py
```

### 测试账号

```
普通用户: 13800000001-13800000005 / test123456
员工:     13900000001-13900000002 / test123456
管理员:   13700000001 / test123456
```

## 并发测试

```bash
cd backend
python tests/test_concurrency.py
```

测试内容：
1. 100用户并发预订同一猫屋，验证只有1个成功
2. 500QPS压力测试
3. 多猫屋并发测试

## 项目结构

```
.
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/             # API路由
│   │   ├── config/          # 配置管理
│   │   ├── core/            # 核心模块（安全、错误、中间件）
│   │   ├── database/        # 数据库连接
│   │   ├── models/          # SQLAlchemy模型
│   │   ├── schemas/         # Pydantic模型
│   │   └── utils/           # 工具类（锁、支付、备份）
│   ├── scripts/             # 脚本
│   ├── tests/               # 测试
│   ├── main.py              # 应用入口
│   └── Dockerfile
├── frontend/                # 前端服务
│   ├── src/
│   │   ├── api/             # API请求
│   │   ├── components/      # 公共组件
│   │   ├── router/          # 路由
│   │   ├── stores/          # 状态管理
│   │   ├── utils/           # 工具函数
│   │   ├── views/           # 页面
│   │   └── types/           # 类型定义
│   └── Dockerfile
├── nginx/                   # Nginx配置
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── .env
└── start.bat
```

## API接口

### 认证接口
- `POST /api/v1/auth/login` - 登录
- `POST /api/v1/auth/register` - 注册
- `GET /api/v1/auth/me` - 获取当前用户

### 猫屋接口
- `GET /api/v1/cat-rooms` - 猫屋列表
- `GET /api/v1/cat-rooms/availability` - 查询可用猫屋
- `GET /api/v1/cat-rooms/{id}` - 猫屋详情
- `POST /api/v1/cat-rooms` - 创建猫屋（管理员）
- `PUT /api/v1/cat-rooms/{id}` - 更新猫屋（管理员）
- `DELETE /api/v1/cat-rooms/{id}` - 删除猫屋（管理员）

### 预订接口
- `POST /api/v1/bookings` - 创建预订（核心）
- `GET /api/v1/bookings` - 我的预订列表
- `GET /api/v1/bookings/all` - 所有预订（员工）
- `GET /api/v1/bookings/{id}` - 预订详情
- `POST /api/v1/bookings/{id}/verify` - 扫码核销
- `POST /api/v1/bookings/{id}/checkout` - 退房
- `POST /api/v1/bookings/{id}/add-service` - 加购服务
- `POST /api/v1/bookings/{id}/cancel` - 取消预订
- `GET /api/v1/bookings/{id}/qrcode` - 获取核销码二维码
- `GET /api/v1/bookings/{id}/refund` - 获取可退款金额

### 服务接口
- `GET /api/v1/services` - 服务列表
- `POST /api/v1/services` - 创建服务（管理员）
- `PUT /api/v1/services/{id}` - 更新服务（管理员）
- `DELETE /api/v1/services/{id}` - 删除服务（管理员）

### 会员接口
- `GET /api/v1/members/me` - 我的会员信息
- `POST /api/v1/members/recharge` - 会员充值
- `GET /api/v1/members/points` - 积分记录
- `POST /api/v1/members/points/exchange` - 积分兑换

## 配置说明

### 环境变量（.env）

```env
# 数据库
POSTGRES_DB=cat_hotel
POSTGRES_USER=cat_hotel
POSTGRES_PASSWORD=cat_hotel_2024

# Redis
REDIS_PASSWORD=redis_cat_hotel_2024

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 退款规则
REFUND_DAYS_FULL=7
REFUND_DAYS_PARTIAL=3
REFUND_RATE_PARTIAL=0.8

# 备份
BACKUP_SCHEDULE=0 2 * * *
BACKUP_DIR=/backup
CLOUD_STORAGE_ENDPOINT=
CLOUD_STORAGE_BUCKET=
CLOUD_STORAGE_ACCESS_KEY=
CLOUD_STORAGE_SECRET_KEY=
```

## 安全特性

1. **JWT认证** - 无状态身份认证
2. **密码哈希** - bcrypt算法存储密码
3. **RBAC权限控制** - 用户/员工/管理员三级权限
4. **SQL注入防护** - SQLAlchemy ORM预编译
5. **XSS防护** - 输入验证和输出编码
6. **CORS配置** - 跨域安全控制
7. **安全头** - HSTS、X-Frame-Options等
8. **限流** - IP级和全局请求限流

## 监控和日志

- 请求ID链路追踪
- 结构化日志输出
- 健康检查接口 `/health`
- 数据库和Redis连接状态监控
- 定时任务执行日志

## 常用命令

```bash
# 启动服务
docker-compose up -d --build

# 查看日志
docker-compose logs -f
docker-compose logs backend

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 进入容器
docker-compose exec backend bash
docker-compose exec postgres psql -U cat_hotel -d cat_hotel

# 数据库备份
docker-compose exec backend python -c "import asyncio; from app.utils.backup import backup_service; asyncio.run(backup_service.create_backup())"

# 运行测试
cd backend
pytest tests/
```

## 许可证

MIT
