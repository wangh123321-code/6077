import asyncio
import sys
import os
from datetime import date, timedelta, time
from decimal import Decimal
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.session import db_manager
from app.models.user import User, UserRole
from app.models.schedule import (
    Employee,
    Shift,
    ShiftType,
    SchedulingRule,
    SkillTag,
)


DEFAULT_SHIFTS = [
    {
        "name": "早班",
        "shift_type": ShiftType.MORNING,
        "start_time": time(8, 0),
        "end_time": time(16, 0),
        "min_staff": 3,
        "max_staff": 5,
        "required_skills": [SkillTag.CAT_CARE],
        "color": "#67C23A",
        "remark": "8:00 - 16:00，日间主要工作",
    },
    {
        "name": "中班",
        "shift_type": ShiftType.AFTERNOON,
        "start_time": time(16, 0),
        "end_time": time(0, 0),
        "min_staff": 2,
        "max_staff": 4,
        "required_skills": [SkillTag.CAT_CARE, SkillTag.RECEPTION],
        "color": "#E6A23C",
        "remark": "16:00 - 24:00，下午和晚间服务",
    },
    {
        "name": "晚班",
        "shift_type": ShiftType.NIGHT,
        "start_time": time(0, 0),
        "end_time": time(8, 0),
        "min_staff": 1,
        "max_staff": 2,
        "required_skills": [SkillTag.NIGHT_SHIFT, SkillTag.EMERGENCY],
        "color": "#F56C6C",
        "remark": "24:00 - 8:00，夜间值守",
    },
]

DEFAULT_RULE = {
    "name": "默认排班规则",
    "weekly_rest_days": 2,
    "max_consecutive_days": 5,
    "daily_max_hours": Decimal("8.0"),
    "weekly_max_hours": Decimal("40.0"),
    "min_break_hours_between_shifts": Decimal("12.0"),
    "night_shift_premium": Decimal("1.5"),
    "weekend_premium": Decimal("1.2"),
    "holiday_premium": Decimal("2.0"),
    "preference_weight": 10,
    "skill_weight": 20,
    "workload_weight": 30,
    "history_weight": 15,
    "is_default": True,
    "remark": "系统默认排班规则，适用于大多数情况",
}

EMPLOYEE_SKILLS = [
    [SkillTag.CAT_CARE, SkillTag.CLEANING],
    [SkillTag.CAT_CARE, SkillTag.MEDICATION, SkillTag.EMERGENCY],
    [SkillTag.RECEPTION, SkillTag.CAT_CARE, SkillTag.CLEANING],
    [SkillTag.CAT_CARE, SkillTag.NIGHT_SHIFT, SkillTag.EMERGENCY],
    [SkillTag.CAT_CARE, SkillTag.MEDICATION],
    [SkillTag.CLEANING, SkillTag.CAT_CARE, SkillTag.RECEPTION],
    [SkillTag.CAT_CARE, SkillTag.EMERGENCY, SkillTag.NIGHT_SHIFT],
    [SkillTag.CLEANING, SkillTag.CAT_CARE],
    [SkillTag.MEDICATION, SkillTag.CAT_CARE, SkillTag.EMERGENCY],
    [SkillTag.RECEPTION, SkillTag.CAT_CARE],
    [SkillTag.CAT_CARE, SkillTag.NIGHT_SHIFT, SkillTag.MEDICATION],
    [SkillTag.CLEANING, SkillTag.CAT_CARE],
    [SkillTag.CAT_CARE, SkillTag.EMERGENCY, SkillTag.MEDICATION],
    [SkillTag.RECEPTION, SkillTag.NIGHT_SHIFT, SkillTag.CAT_CARE],
    [SkillTag.CAT_CARE, SkillTag.CLEANING],
    [SkillTag.MEDICATION, SkillTag.NIGHT_SHIFT, SkillTag.EMERGENCY],
    [SkillTag.CAT_CARE, SkillTag.RECEPTION, SkillTag.CLEANING],
    [SkillTag.CAT_CARE, SkillTag.EMERGENCY],
    [SkillTag.NIGHT_SHIFT, SkillTag.CAT_CARE, SkillTag.MEDICATION],
    [SkillTag.CAT_CARE, SkillTag.CLEANING, SkillTag.RECEPTION],
]

EMPLOYEE_NAMES = [
    "张小明", "李小红", "王大伟", "赵丽丽", "刘建国",
    "陈美玲", "杨志强", "黄雅婷", "周俊杰", "吴晓燕",
    "郑海涛", "孙梦琪", "钱志刚", "冯雪梅", "褚浩然",
    "卫佳丽", "蒋晓峰", "沈云霞", "韩子轩", "朱丽娟",
]

EMPLOYEE_DEPARTMENTS = [
    "护理部", "护理部", "前台", "护理部", "护理部",
    "清洁部", "护理部", "护理部", "护理部", "前台",
    "护理部", "清洁部", "护理部", "前台", "护理部",
    "护理部", "护理部", "护理部", "护理部", "清洁部",
]

EMPLOYEE_POSITIONS = [
    "护理员", "护理组长", "前台接待", "护理员", "护理员",
    "清洁员", "护理员", "护理员", "护理组长", "前台主管",
    "护理员", "清洁员", "护理员", "前台接待", "护理员",
    "护理员", "护理员", "护理员", "护理员", "清洁组长",
]


async def create_default_shifts(db: AsyncSession) -> List[Shift]:
    print("创建默认班次...")
    result = await db.execute(select(func.count(Shift.id)))
    count = result.scalar_one()

    if count > 0:
        print(f"  班次已存在 {count} 条记录，跳过创建\n")
        result = await db.execute(select(Shift))
        return list(result.scalars().all())

    created_shifts = []
    for shift_data in DEFAULT_SHIFTS:
        shift = Shift(**shift_data)
        db.add(shift)
        created_shifts.append(shift)
        print(f"  创建班次: {shift_data['name']} - "
              f"{shift_data['start_time'].strftime('%H:%M')} ~ "
              f"{shift_data['end_time'].strftime('%H:%M')} - "
              f"最少{shift_data['min_staff']}人")

    await db.flush()
    print(f"  共创建 {len(created_shifts)} 个班次\n")
    return created_shifts


async def create_default_rule(db: AsyncSession) -> SchedulingRule:
    print("创建默认排班规则...")
    result = await db.execute(
        select(SchedulingRule).where(SchedulingRule.is_default == True)
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  默认规则已存在: {existing.name}\n")
        return existing

    rule = SchedulingRule(**DEFAULT_RULE)
    db.add(rule)
    await db.flush()
    print(f"  创建规则: {DEFAULT_RULE['name']}\n")
    return rule


async def create_staff_users(db: AsyncSession) -> List[User]:
    print("创建员工用户...")
    
    staff_users = []
    for i in range(20):
        phone = f"139{10000000 + i:08d}"
        result = await db.execute(select(User).where(User.phone == phone))
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"  用户已存在: {phone} ({EMPLOYEE_NAMES[i]})")
            staff_users.append(existing)
            continue

        user = User(
            phone=phone,
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYGyJkHdKXj5GKC",
            nickname=EMPLOYEE_NAMES[i],
            role=UserRole.STAFF,
        )
        db.add(user)
        staff_users.append(user)
        print(f"  创建用户: {phone} ({EMPLOYEE_NAMES[i]})")

    await db.flush()
    print(f"  共处理 {len(staff_users)} 个员工用户\n")
    return staff_users


async def create_employees(db: AsyncSession, staff_users: List[User]) -> List[Employee]:
    print("创建员工档案...")
    result = await db.execute(select(func.count(Employee.id)))
    count = result.scalar_one()

    if count > 0:
        print(f"  员工档案已存在 {count} 条记录，跳过创建\n")
        result = await db.execute(select(Employee))
        return list(result.scalars().all())

    created_employees = []
    today = date.today()
    
    for i, user in enumerate(staff_users[:20]):
        hire_date = today - timedelta(days=365 * (i % 3 + 1))
        
        preferred_shift = None
        if i % 3 == 0:
            preferred_shift = ShiftType.MORNING
        elif i % 3 == 1:
            preferred_shift = ShiftType.AFTERNOON
        
        unavailable_days = []
        if i % 7 == 0:
            unavailable_days = ["saturday", "sunday"]
        
        weekly_rest_days = 2
        if i % 5 == 0:
            weekly_rest_days = 1
        
        max_consecutive_days = 5
        if i % 4 == 0:
            max_consecutive_days = 4

        employee = Employee(
            user_id=user.id,
            employee_no=f"EMP{2024}{i+1:04d}",
            department=EMPLOYEE_DEPARTMENTS[i],
            position=EMPLOYEE_POSITIONS[i],
            hire_date=hire_date,
            weekly_rest_days=weekly_rest_days,
            max_consecutive_days=max_consecutive_days,
            preferred_shift_type=preferred_shift,
            unavailable_days=unavailable_days,
            skills=EMPLOYEE_SKILLS[i],
            is_active=True,
            remark=f"员工编号 EMP{2024}{i+1:04d}",
        )
        db.add(employee)
        created_employees.append(employee)
        
        preferred_str = preferred_shift.value if preferred_shift else "无偏好"
        print(f"  创建员工: {EMPLOYEE_NAMES[i]} - "
              f"{EMPLOYEE_DEPARTMENTS[i]} - "
              f"{EMPLOYEE_POSITIONS[i]} - "
              f"班次偏好: {preferred_str}")

    await db.flush()
    print(f"  共创建 {len(created_employees)} 名员工\n")
    return created_employees


async def init_schedule_data():
    print("=" * 60)
    print("猫咪民宿智能排班系统 - 初始化数据")
    print("=" * 60 + "\n")

    print("初始化数据库连接...")
    db_manager.init_engine()
    print(f"  数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}\n")

    async with db_manager.get_session_factory()() as db:
        try:
            shifts = await create_default_shifts(db)
            rule = await create_default_rule(db)
            staff_users = await create_staff_users(db)
            employees = await create_employees(db, staff_users)

            await db.commit()

            print("=" * 60)
            print("排班模块初始化完成!")
            print("=" * 60)
            print("\n数据统计:")
            print(f"  班次数量: {len(shifts)}")
            for shift in shifts:
                print(f"    - {shift.name}: "
                      f"{shift.start_time.strftime('%H:%M')} ~ "
                      f"{shift.end_time.strftime('%H:%M')} "
                      f"(最少{shift.min_staff}人)")
            print(f"  排班规则: {rule.name}")
            print(f"  员工数量: {len(employees)}")

            print("\n员工登录账号:")
            for i in range(min(5, len(staff_users))):
                print(f"  {EMPLOYEE_NAMES[i]}: {staff_users[i].phone} / test123456")
            print("  (更多员工账号: 13910000000 ~ 13910000019, 密码统一为 test123456)")

            print("\n排班规则说明:")
            print(f"  - 每周休息天数: {rule.weekly_rest_days}天")
            print(f"  - 连续上班不超过: {rule.max_consecutive_days}天")
            print(f"  - 每日最大工时: {rule.daily_max_hours}小时")
            print(f"  - 每周最大工时: {rule.weekly_max_hours}小时")
            print(f"  - 班次间最少休息: {rule.min_break_hours_between_shifts}小时")
            print(f"  - 晚班补贴系数: {rule.night_shift_premium}x")
            print(f"  - 周末补贴系数: {rule.weekend_premium}x")
            print(f"  - 节假日补贴系数: {rule.holiday_premium}x")

            print("\n智能排班算法权重:")
            print(f"  - 班次偏好权重: {rule.preference_weight}%")
            print(f"  - 技能匹配权重: {rule.skill_weight}%")
            print(f"  - 工作量均衡权重: {rule.workload_weight}%")
            print(f"  - 历史排班权重: {rule.history_weight}%")

            print("\n" + "=" * 60)

        except Exception as e:
            await db.rollback()
            print(f"\n错误: 初始化失败 - {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await db_manager.close()


async def clear_schedule_data():
    print("=" * 60)
    print("清除排班模块数据")
    print("=" * 60 + "\n")

    confirm = input("确定要清除所有排班模块数据吗？此操作不可恢复! (yes/no): ")
    if confirm.lower() != "yes":
        print("操作已取消")
        return

    print("初始化数据库连接...")
    db_manager.init_engine()

    async with db_manager.get_session_factory()() as db:
        try:
            from sqlalchemy import delete
            from app.models.schedule import (
                Schedule, LeaveRequest, ShiftSwap, ShiftPreference,
                Attendance, AttendanceAlert,
            )

            print("清除考勤提醒数据...")
            await db.execute(delete(AttendanceAlert))

            print("清除考勤数据...")
            await db.execute(delete(Attendance))

            print("清除班次偏好数据...")
            await db.execute(delete(ShiftPreference))

            print("清除调班申请数据...")
            await db.execute(delete(ShiftSwap))

            print("清除请假申请数据...")
            await db.execute(delete(LeaveRequest))

            print("清除排班记录...")
            await db.execute(delete(Schedule))

            print("清除员工档案...")
            await db.execute(delete(Employee))

            print("清除排班规则...")
            await db.execute(delete(SchedulingRule))

            print("清除班次数据...")
            await db.execute(delete(Shift))

            await db.commit()

            print("\n所有排班模块数据已清除!")

        except Exception as e:
            await db.rollback()
            print(f"\n错误: 清除失败 - {str(e)}")
            raise
        finally:
            await db_manager.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        asyncio.run(clear_schedule_data())
    else:
        asyncio.run(init_schedule_data())
