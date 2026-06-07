import asyncio
import sys
import os
from datetime import date, timedelta
from decimal import Decimal
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.session import db_manager
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.cat_room import CatRoom, CatRoomStatus
from app.models.service import Service, ServiceType
from app.models.booking import Booking, BookingStatus
from app.models.booking_service import BookingService, BookingServiceStatus
from app.models.member import Member, MemberLevel
from app.models.payment import Payment, PaymentMethod, PaymentStatus


DEFAULT_PASSWORD = "test123456"

TEST_USERS = [
    {"phone": "13800000001", "password": DEFAULT_PASSWORD, "nickname": "测试用户1", "role": UserRole.USER},
    {"phone": "13800000002", "password": DEFAULT_PASSWORD, "nickname": "测试用户2", "role": UserRole.USER},
    {"phone": "13800000003", "password": DEFAULT_PASSWORD, "nickname": "测试用户3", "role": UserRole.USER},
    {"phone": "13800000004", "password": DEFAULT_PASSWORD, "nickname": "测试用户4", "role": UserRole.USER},
    {"phone": "13800000005", "password": DEFAULT_PASSWORD, "nickname": "测试用户5", "role": UserRole.USER},
    {"phone": "13900000001", "password": DEFAULT_PASSWORD, "nickname": "员工小王", "role": UserRole.STAFF},
    {"phone": "13900000002", "password": DEFAULT_PASSWORD, "nickname": "员工小李", "role": UserRole.STAFF},
    {"phone": "13700000001", "password": DEFAULT_PASSWORD, "nickname": "管理员", "role": UserRole.ADMIN},
]

TEST_CAT_ROOMS = [
    {"name": "豪华大床房", "description": "宽敞舒适的独立房间，配备观景窗台和高级猫爬架", "price_per_day": Decimal("198.00"),
     "facilities": ["独立空调", "自动饮水机", "高清摄像头", "猫爬架", "观景窗台"],
     "images": ["/images/room1_1.jpg", "/images/room1_2.jpg"],
     "status": CatRoomStatus.AVAILABLE, "area": Decimal("8.5"), "floor": 2, "location": "A区201"},
    {"name": "标准单人间", "description": "温馨舒适的标准房间，适合单只猫咪入住", "price_per_day": Decimal("128.00"),
     "facilities": ["独立空调", "自动饮水机", "猫窝", "玩具"],
     "images": ["/images/room2_1.jpg", "/images/room2_2.jpg"],
     "status": CatRoomStatus.AVAILABLE, "area": Decimal("5.0"), "floor": 1, "location": "A区101"},
    {"name": "家庭套房", "description": "超大空间，适合多只猫咪或家庭入住", "price_per_day": Decimal("298.00"),
     "facilities": ["独立空调", "双自动饮水机", "高清摄像头x2", "大型猫爬架", "观景阳台"],
     "images": ["/images/room3_1.jpg", "/images/room3_2.jpg"],
     "status": CatRoomStatus.AVAILABLE, "area": Decimal("12.0"), "floor": 3, "location": "B区301"},
    {"name": "阳光房", "description": "落地窗设计，充足自然采光，猫咪最爱", "price_per_day": Decimal("168.00"),
     "facilities": ["落地窗", "自动饮水机", "吊床", "猫爬架", "阳光露台"],
     "images": ["/images/room4_1.jpg", "/images/room4_2.jpg"],
     "status": CatRoomStatus.AVAILABLE, "area": Decimal("6.5"), "floor": 2, "location": "A区202"},
    {"name": "经济房", "description": "经济实惠的选择，基本配置齐全", "price_per_day": Decimal("88.00"),
     "facilities": ["独立空调", "饮水机", "猫窝", "基础玩具"],
     "images": ["/images/room5_1.jpg"],
     "status": CatRoomStatus.AVAILABLE, "area": Decimal("4.0"), "floor": 1, "location": "B区101"},
    {"name": "VIP总统套房", "description": "顶级配置，专属管家服务，至尊享受", "price_per_day": Decimal("498.00"),
     "facilities": ["独立空调", "智能喂食器", "24小时监控", "豪华猫爬架", "专属管家", "空气净化器"],
     "images": ["/images/room6_1.jpg", "/images/room6_2.jpg", "/images/room6_3.jpg"],
     "status": CatRoomStatus.AVAILABLE, "area": Decimal("15.0"), "floor": 3, "location": "B区302"},
    {"name": "猫咖互动区", "description": "开放式空间，适合爱社交的猫咪", "price_per_day": Decimal("68.00"),
     "facilities": ["共享空间", "多种玩具", "猫爬架群落", "互动隧道"],
     "images": ["/images/room7_1.jpg"],
     "status": CatRoomStatus.AVAILABLE, "area": Decimal("20.0"), "floor": 1, "location": "C区101"},
    {"name": "康复护理房", "description": "专业护理环境，适合术后康复或老年猫咪", "price_per_day": Decimal("258.00"),
     "facilities": ["恒温恒湿", "医疗监控", "护理床", "专业护理人员", "定时喂药"],
     "images": ["/images/room8_1.jpg"],
     "status": CatRoomStatus.AVAILABLE, "area": Decimal("6.0"), "floor": 1, "location": "医疗区101"},
    {"name": "猫咪产房", "description": "专为孕猫和新生小猫设计的温馨空间", "price_per_day": Decimal("228.00"),
     "facilities": ["恒温箱", "育婴区", "24小时监控", "专业护理", "营养配餐"],
     "images": ["/images/room9_1.jpg"],
     "status": CatRoomStatus.AVAILABLE, "area": Decimal("7.0"), "floor": 2, "location": "医疗区201"},
    {"name": "短租钟点房", "description": "按小时计费，适合临时托管需求", "price_per_day": Decimal("50.00"),
     "facilities": ["独立空间", "饮水机", "临时猫窝"],
     "images": ["/images/room10_1.jpg"],
     "status": CatRoomStatus.AVAILABLE, "area": Decimal("3.0"), "floor": 1, "location": "C区102"},
]

TEST_SERVICES = [
    {"name": "基础洗浴", "description": "清洁毛发、修剪指甲、清洁耳道", "price": Decimal("88.00"),
     "type": ServiceType.BASIC, "duration": 60, "applicable_scene": "日常护理"},
    {"name": "SPA护理", "description": "深层清洁、精油按摩、皮毛护理", "price": Decimal("198.00"),
     "type": ServiceType.BASIC, "duration": 90, "applicable_scene": "深度护理"},
    {"name": "美容造型", "description": "专业造型修剪，打造可爱造型", "price": Decimal("158.00"),
     "type": ServiceType.BASIC, "duration": 120, "applicable_scene": "美容造型"},
    {"name": "健康体检", "description": "基础健康检查，包括体温、体重、心肺听诊", "price": Decimal("128.00"),
     "type": ServiceType.BASIC, "duration": 30, "applicable_scene": "健康管理"},
    {"name": "疫苗接种", "description": "常规疫苗接种服务", "price": Decimal("98.00"),
     "type": ServiceType.BASIC, "duration": 20, "applicable_scene": "健康管理"},
    {"name": "驱虫服务", "description": "体内外驱虫，预防寄生虫", "price": Decimal("68.00"),
     "type": ServiceType.BASIC, "duration": 15, "applicable_scene": "健康管理"},
    {"name": "加餐服务", "description": "提供高级猫粮或罐头", "price": Decimal("38.00"),
     "type": ServiceType.ADDON, "duration": 5, "applicable_scene": "日常护理"},
    {"name": "陪玩服务", "description": "专人陪玩30分钟，消耗精力", "price": Decimal("48.00"),
     "type": ServiceType.ADDON, "duration": 30, "applicable_scene": "互动娱乐"},
    {"name": "直播服务", "description": "专属直播通道，随时查看爱宠", "price": Decimal("28.00"),
     "type": ServiceType.ADDON, "duration": 1440, "applicable_scene": "远程查看"},
    {"name": "接送服务", "description": "上门接送猫咪", "price": Decimal("58.00"),
     "type": ServiceType.ADDON, "duration": 60, "applicable_scene": "交通服务"},
]


async def create_test_users(db: AsyncSession) -> List[User]:
    print("创建测试用户...")
    created_users = []
    for user_data in TEST_USERS:
        result = await db.execute(select(User).where(User.phone == user_data["phone"]))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"  用户已存在: {user_data['phone']} ({user_data['role'].value})")
            created_users.append(existing)
            continue

        hashed_pw = hash_password(user_data["password"])
        user = User(
            phone=user_data["phone"],
            password_hash=hashed_pw,
            nickname=user_data["nickname"],
            role=user_data["role"]
        )
        db.add(user)
        created_users.append(user)
        print(f"  创建用户: {user_data['phone']} ({user_data['role'].value}) - {user_data['nickname']}")

    await db.flush()
    print(f"  共处理 {len(created_users)} 个用户\n")
    return created_users


async def create_cat_rooms(db: AsyncSession) -> List[CatRoom]:
    print("创建猫屋数据...")
    result = await db.execute(select(func.count(CatRoom.id)))
    count = result.scalar_one()

    if count > 0:
        print(f"  猫屋已存在 {count} 条记录，跳过创建\n")
        result = await db.execute(select(CatRoom))
        return list(result.scalars().all())

    created_rooms = []
    for room_data in TEST_CAT_ROOMS:
        room = CatRoom(**room_data)
        db.add(room)
        created_rooms.append(room)
        print(f"  创建猫屋: {room_data['name']} - {room_data['price_per_day']}元/天")

    await db.flush()
    print(f"  共创建 {len(created_rooms)} 个猫屋\n")
    return created_rooms


async def create_services(db: AsyncSession) -> List[Service]:
    print("创建服务数据...")
    result = await db.execute(select(func.count(Service.id)))
    count = result.scalar_one()

    if count > 0:
        print(f"  服务已存在 {count} 条记录，跳过创建\n")
        result = await db.execute(select(Service))
        return list(result.scalars().all())

    created_services = []
    for service_data in TEST_SERVICES:
        service = Service(**service_data)
        db.add(service)
        created_services.append(service)
        print(f"  创建服务: {service_data['name']} - {service_data['price']}元")

    await db.flush()
    print(f"  共创建 {len(created_services)} 个服务\n")
    return created_services


async def create_test_members(db: AsyncSession, users: List[User]) -> List[Member]:
    print("创建会员数据...")
    created_members = []

    regular_users = [u for u in users if u.role == UserRole.USER]

    for i, user in enumerate(regular_users[:3]):
        result = await db.execute(select(Member).where(Member.user_id == user.id))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"  会员已存在: 用户ID={user.id}")
            created_members.append(existing)
            continue

        levels = [MemberLevel.BRONZE, MemberLevel.SILVER, MemberLevel.GOLD]
        member = Member(
            user_id=user.id,
            level=levels[i % len(levels)],
            points=1000 * (i + 1),
            total_spent=Decimal(str(500 * (i + 1)))
        )
        db.add(member)
        created_members.append(member)
        print(f"  创建会员: 用户ID={user.id}, 等级={levels[i].value}, 积分={member.points}")

    await db.flush()
    print(f"  共创建 {len(created_members)} 个会员\n")
    return created_members


async def create_test_bookings(db: AsyncSession, users: List[User], rooms: List[CatRoom], services: List[Service]) -> List[Booking]:
    print("创建测试订单...")
    created_bookings = []

    regular_users = [u for u in users if u.role == UserRole.USER]
    if not regular_users or not rooms:
        print("  缺少用户或猫屋数据，跳过订单创建\n")
        return []

    today = date.today()
    booking_scenarios = [
        {"user_idx": 0, "room_idx": 0, "days": 3, "offset": 2, "status": BookingStatus.CONFIRMED, "has_payment": True},
        {"user_idx": 1, "room_idx": 1, "days": 5, "offset": 5, "status": BookingStatus.PAID, "has_payment": True},
        {"user_idx": 0, "room_idx": 2, "days": 2, "offset": 0, "status": BookingStatus.CHECKED_IN, "has_payment": True},
        {"user_idx": 2, "room_idx": 3, "days": 7, "offset": -10, "status": BookingStatus.CHECKED_OUT, "has_payment": True},
        {"user_idx": 1, "room_idx": 4, "days": 1, "offset": 10, "status": BookingStatus.PENDING, "has_payment": False},
        {"user_idx": 0, "room_idx": 1, "days": 4, "offset": 30, "status": BookingStatus.CONFIRMED, "has_payment": True},
    ]

    for i, scenario in enumerate(booking_scenarios):
        user = regular_users[scenario["user_idx"] % len(regular_users)]
        room = rooms[scenario["room_idx"] % len(rooms)]

        check_in = today + timedelta(days=scenario["offset"])
        check_out = check_in + timedelta(days=scenario["days"])

        result = await db.execute(
            select(func.count(Booking.id)).where(
                Booking.user_id == user.id,
                Booking.cat_room_id == room.id,
                Booking.check_in_date == check_in
            )
        )
        existing_count = result.scalar_one()
        if existing_count > 0:
            print(f"  订单已存在: 用户={user.id}, 猫屋={room.id}, 日期={check_in}")
            continue

        total_price = room.price_per_day * scenario["days"]

        booking = Booking(
            order_no=f"CH{today.strftime('%Y%m%d')}{10000 + i:05d}",
            user_id=user.id,
            cat_room_id=room.id,
            check_in_date=check_in,
            check_out_date=check_out,
            cat_name=f"咪咪{i+1}",
            cat_age=2 + i,
            cat_food_brand="皇家" if i % 2 == 0 else "渴望",
            special_requirements="需要定时喂食" if i % 3 == 0 else None,
            status=scenario["status"],
            total_price=total_price,
            verify_code=f"VERIFY{i+1:08d}" if scenario["status"] != BookingStatus.CANCELLED else None
        )
        db.add(booking)
        await db.flush()

        if i < len(services) and scenario["has_payment"]:
            addon_service = BookingService(
                booking_id=booking.id,
                service_id=services[i % len(services)].id,
                quantity=1,
                price=services[i % len(services)].price,
                status=BookingServiceStatus.COMPLETED if scenario["status"] == BookingStatus.CHECKED_OUT else BookingServiceStatus.PENDING
            )
            db.add(addon_service)
            booking.total_price += services[i % len(services)].price

        if scenario["has_payment"]:
            payment = Payment(
                order_no=booking.order_no,
                user_id=user.id,
                amount=booking.total_price,
                payment_method=PaymentMethod.ALIPAY if i % 2 == 0 else PaymentMethod.WECHAT,
                status=PaymentStatus.SUCCESS,
                transaction_id=f"TXN{i+1:010d}"
            )
            db.add(payment)

        created_bookings.append(booking)
        print(f"  创建订单: {booking.order_no} - {room.name} - {scenario['status'].value} - {booking.total_price}元")

    await db.flush()
    print(f"  共创建 {len(created_bookings)} 个订单\n")
    return created_bookings


async def init_test_data():
    print("=" * 60)
    print("猫咪民宿预订系统 - 测试数据初始化")
    print("=" * 60 + "\n")

    print("初始化数据库连接...")
    db_manager.init_engine()
    print(f"  数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}\n")

    async with db_manager.get_session_factory()() as db:
        try:
            users = await create_test_users(db)
            rooms = await create_cat_rooms(db)
            services = await create_services(db)
            members = await create_test_members(db, users)
            bookings = await create_test_bookings(db, users, rooms, services)

            await db.commit()

            print("=" * 60)
            print("测试数据初始化完成!")
            print("=" * 60)
            print("\n数据统计:")
            print(f"  用户数: {len(users)}")
            print(f"    - 普通用户: {len([u for u in users if u.role == UserRole.USER])}")
            print(f"    - 员工: {len([u for u in users if u.role == UserRole.STAFF])}")
            print(f"    - 管理员: {len([u for u in users if u.role == UserRole.ADMIN])}")
            print(f"  猫屋数: {len(rooms)}")
            print(f"  服务数: {len(services)}")
            print(f"  会员数: {len(members)}")
            print(f"  订单数: {len(bookings)}")

            print("\n测试账号:")
            for user_data in TEST_USERS:
                role_name = {"user": "用户", "staff": "员工", "admin": "管理员"}[user_data["role"].value]
                print(f"  {role_name}: {user_data['phone']} / {DEFAULT_PASSWORD}")

            print("\n" + "=" * 60)

        except Exception as e:
            await db.rollback()
            print(f"\n错误: 初始化失败 - {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await db_manager.close()


async def clear_test_data():
    print("=" * 60)
    print("清除测试数据")
    print("=" * 60 + "\n")

    confirm = input("确定要清除所有测试数据吗？此操作不可恢复! (yes/no): ")
    if confirm.lower() != "yes":
        print("操作已取消")
        return

    print("初始化数据库连接...")
    db_manager.init_engine()

    async with db_manager.get_session_factory()() as db:
        try:
            from sqlalchemy import delete

            print("清除订单服务关联数据...")
            await db.execute(delete(BookingService))

            print("清除支付数据...")
            await db.execute(delete(Payment))

            print("清除订单数据...")
            await db.execute(delete(Booking))

            print("清除会员数据...")
            await db.execute(delete(Member))

            print("清除用户数据...")
            await db.execute(delete(User))

            print("清除服务数据...")
            await db.execute(delete(Service))

            print("清除猫屋数据...")
            await db.execute(delete(CatRoom))

            await db.commit()

            print("\n所有测试数据已清除!")

        except Exception as e:
            await db.rollback()
            print(f"\n错误: 清除失败 - {str(e)}")
            raise
        finally:
            await db_manager.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        asyncio.run(clear_test_data())
    else:
        asyncio.run(init_test_data())
