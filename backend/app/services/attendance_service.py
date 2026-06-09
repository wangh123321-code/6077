"""
考勤服务模块
处理员工打卡、考勤状态计算、异常提醒等功能
"""
import logging
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.models import (
    Employee,
    Schedule,
    Shift,
    Attendance,
    AttendanceAlert,
    AttendanceStatus,
    AlertType,
    LeaveRequest,
    RequestStatus,
    User,
)

logger = logging.getLogger(__name__)


async def get_employee_by_user_id(db: AsyncSession, user_id: int) -> Optional[Employee]:
    """根据用户ID获取员工信息"""
    query = select(Employee).where(Employee.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_or_create_attendance(db: AsyncSession, employee_id: int, attendance_date: date) -> Attendance:
    """获取或创建当日考勤记录"""
    query = select(Attendance).where(
        and_(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date == attendance_date,
        )
    )
    result = await db.execute(query)
    attendance = result.scalar_one_or_none()

    if not attendance:
        schedule_query = select(Schedule).where(
            and_(
                Schedule.employee_id == employee_id,
                Schedule.schedule_date == attendance_date,
            )
        )
        schedule_result = await db.execute(schedule_query)
        schedule = schedule_result.scalar_one_or_none()

        attendance = Attendance(
            employee_id=employee_id,
            schedule_id=schedule.id if schedule else None,
            attendance_date=attendance_date,
            status=AttendanceStatus.ABSENT,
        )
        db.add(attendance)
        await db.flush()

    return attendance


def calculate_shift_duration(start_time: time, end_time: time) -> Decimal:
    """计算班次时长"""
    start_dt = datetime.combine(date.today(), start_time)
    end_dt = datetime.combine(date.today(), end_time)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    hours = (end_dt - start_dt).total_seconds() / 3600
    return Decimal(str(round(hours, 2)))


def calculate_status(
    check_in: Optional[datetime],
    check_out: Optional[datetime],
    schedule: Optional[Schedule],
    shift: Optional[Shift],
    is_leave: bool,
) -> Tuple[AttendanceStatus, int, int, Decimal, Decimal]:
    """计算考勤状态"""
    if is_leave:
        return AttendanceStatus.LEAVE, 0, 0, Decimal('0'), Decimal('0')

    if not check_in and not check_out:
        return AttendanceStatus.ABSENT, 0, 0, Decimal('0'), Decimal('0')

    late_minutes = 0
    early_leave_minutes = 0
    work_hours = Decimal('0')
    overtime_hours = Decimal('0')

    if check_in and check_out:
        duration = (check_out - check_in).total_seconds() / 3600
        work_hours = Decimal(str(round(duration, 2)))

        if shift and schedule:
            scheduled_start = datetime.combine(schedule.schedule_date, shift.start_time)
            scheduled_end = datetime.combine(schedule.schedule_date, shift.end_time)
            if scheduled_end <= scheduled_start:
                scheduled_end += timedelta(days=1)

            if check_in > scheduled_start:
                late_minutes = int((check_in - scheduled_start).total_seconds() / 60)

            if check_out < scheduled_end:
                early_leave_minutes = int((scheduled_end - check_out).total_seconds() / 60)

            shift_duration = calculate_shift_duration(shift.start_time, shift.end_time)
            if work_hours > shift_duration:
                overtime_hours = work_hours - shift_duration

    status = AttendanceStatus.ON_TIME
    if late_minutes > 0 and early_leave_minutes > 0:
        status = AttendanceStatus.LATE if late_minutes >= early_leave_minutes else AttendanceStatus.EARLY_LEAVE
    elif late_minutes > 0:
        status = AttendanceStatus.LATE
    elif early_leave_minutes > 0:
        status = AttendanceStatus.EARLY_LEAVE

    return status, late_minutes, early_leave_minutes, work_hours, overtime_hours


async def check_is_leave(db: AsyncSession, employee_id: int, attendance_date: date) -> bool:
    """检查员工当天是否请假"""
    query = select(LeaveRequest).where(
        and_(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status == RequestStatus.APPROVED,
            LeaveRequest.start_date <= attendance_date,
            LeaveRequest.end_date >= attendance_date,
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def check_is_day_off(db: AsyncSession, employee_id: int, attendance_date: date) -> bool:
    """检查员工当天是否休息日"""
    schedule_query = select(Schedule).where(
        and_(
            Schedule.employee_id == employee_id,
            Schedule.schedule_date == attendance_date,
        )
    )
    schedule_result = await db.execute(schedule_query)
    schedule = schedule_result.scalar_one_or_none()

    if schedule:
        return False

    emp_query = select(Employee).where(Employee.id == employee_id)
    emp_result = await db.execute(emp_query)
    employee = emp_result.scalar_one_or_none()

    if employee and attendance_date.weekday() in employee.unavailable_days:
        return True

    return False


async def employee_check_in(
    db: AsyncSession,
    employee_id: int,
    check_in_time: Optional[datetime] = None,
    location: Optional[str] = None,
) -> Attendance:
    """员工上班打卡"""
    if not check_in_time:
        check_in_time = datetime.now()

    attendance_date = check_in_time.date()
    attendance = await get_or_create_attendance(db, employee_id, attendance_date)

    if attendance.check_in:
        raise ValueError("今日已打卡上班")

    attendance.check_in = check_in_time

    is_leave = await check_is_leave(db, employee_id, attendance_date)
    if is_leave:
        attendance.status = AttendanceStatus.LEAVE
        attendance.remark = "请假中打卡"
    else:
        schedule = None
        shift = None
        if attendance.schedule_id:
            schedule_query = select(Schedule).where(Schedule.id == attendance.schedule_id)
            schedule_result = await db.execute(schedule_query)
            schedule = schedule_result.scalar_one_or_none()
            if schedule:
                shift_query = select(Shift).where(Shift.id == schedule.shift_id)
                shift_result = await db.execute(shift_query)
                shift = shift_result.scalar_one_or_none()

        status, late_minutes, _, _, _ = calculate_status(
            check_in_time, attendance.check_out, schedule, shift, is_leave
        )
        attendance.status = status
        attendance.late_minutes = late_minutes

        if late_minutes > 0:
            await create_alert(
                db, employee_id, attendance.id,
                AlertType.LATE_ARRIVAL,
                f"您今日迟到 {late_minutes} 分钟，请尽快到岗"
            )

    if location:
        attendance.remark = f"{attendance.remark or ''} 打卡位置: {location}".strip()

    await db.commit()
    await db.refresh(attendance)

    return attendance


async def employee_check_out(
    db: AsyncSession,
    employee_id: int,
    check_out_time: Optional[datetime] = None,
    location: Optional[str] = None,
) -> Attendance:
    """员工下班打卡"""
    if not check_out_time:
        check_out_time = datetime.now()

    attendance_date = check_out_time.date()
    attendance = await get_or_create_attendance(db, employee_id, attendance_date)

    if not attendance.check_in:
        raise ValueError("请先打卡上班")

    if attendance.check_out:
        raise ValueError("今日已打卡下班")

    attendance.check_out = check_out_time

    is_leave = await check_is_leave(db, employee_id, attendance_date)
    schedule = None
    shift = None

    if attendance.schedule_id:
        schedule_query = select(Schedule).where(Schedule.id == attendance.schedule_id)
        schedule_result = await db.execute(schedule_query)
        schedule = schedule_result.scalar_one_or_none()
        if schedule:
            shift_query = select(Shift).where(Shift.id == schedule.shift_id)
            shift_result = await db.execute(shift_query)
            shift = shift_result.scalar_one_or_none()

    status, late_minutes, early_leave_minutes, work_hours, overtime_hours = calculate_status(
        attendance.check_in, check_out_time, schedule, shift, is_leave
    )

    attendance.status = status
    attendance.late_minutes = late_minutes
    attendance.early_leave_minutes = early_leave_minutes
    attendance.work_hours = work_hours
    attendance.overtime_hours = overtime_hours

    if early_leave_minutes > 0:
        await create_alert(
            db, employee_id, attendance.id,
            AlertType.EARLY_DEPARTURE,
            f"您今日早退 {early_leave_minutes} 分钟"
        )

    if location:
        remark = f"打卡位置: {location}"
        attendance.remark = f"{attendance.remark or ''} {remark}".strip()

    await db.commit()
    await db.refresh(attendance)

    return attendance


async def create_alert(
    db: AsyncSession,
    employee_id: int,
    attendance_id: Optional[int],
    alert_type: AlertType,
    message: str,
) -> AttendanceAlert:
    """创建考勤提醒"""
    alert = AttendanceAlert(
        employee_id=employee_id,
        attendance_id=attendance_id,
        alert_type=alert_type,
        message=message,
    )
    db.add(alert)
    await db.flush()
    return alert


async def send_daily_reminders(db: AsyncSession) -> List[Dict[str, Any]]:
    """发送每日考勤提醒（定时任务调用）"""
    results = []
    now = datetime.now()
    today = now.date()

    query = select(Schedule).where(
        and_(
            Schedule.schedule_date == today,
        )
    ).options(
        selectinload(Schedule.employee),
        selectinload(Schedule.shift),
    )
    result = await db.execute(query)
    schedules = result.scalars().all()

    for schedule in schedules:
        if not schedule.employee or not schedule.shift:
            continue

        shift_start = datetime.combine(today, schedule.shift.start_time)
        reminder_time = shift_start - timedelta(minutes=30)

        if now >= reminder_time and now < shift_start:
            attendance_query = select(Attendance).where(
                and_(
                    Attendance.employee_id == schedule.employee_id,
                    Attendance.attendance_date == today,
                    Attendance.check_in.isnot(None),
                )
            )
            attendance_result = await db.execute(attendance_query)
            attendance = attendance_result.scalar_one_or_none()

            if not attendance:
                alert = await create_alert(
                    db, schedule.employee_id, None,
                    AlertType.NO_CHECK_IN,
                    f"您今天有{schedule.shift.name}（{schedule.shift.start_time.strftime('%H:%M')}），请记得打卡上班"
                )
                results.append({
                    'employee_id': schedule.employee_id,
                    'alert_id': alert.id,
                    'message': alert.message,
                    'sent': False,
                })

    await db.commit()
    return results


async def check_morning_attendance(db: AsyncSession) -> List[Dict[str, Any]]:
    """检查上午考勤情况（定时任务，上班后15分钟检查）"""
    results = []
    now = datetime.now()
    today = now.date()

    query = select(Schedule).where(
        and_(
            Schedule.schedule_date == today,
        )
    ).options(
        selectinload(Schedule.employee),
        selectinload(Schedule.shift),
    )
    result = await db.execute(query)
    schedules = result.scalars().all()

    for schedule in schedules:
        if not schedule.employee or not schedule.shift:
            continue

        shift_start = datetime.combine(today, schedule.shift.start_time)
        check_threshold = shift_start + timedelta(minutes=15)

        if now >= check_threshold:
            attendance_query = select(Attendance).where(
                and_(
                    Attendance.employee_id == schedule.employee_id,
                    Attendance.attendance_date == today,
                )
            )
            attendance_result = await db.execute(attendance_query)
            attendance = attendance_result.scalar_one_or_none()

            if not attendance or not attendance.check_in:
                if not attendance:
                    attendance = Attendance(
                        employee_id=schedule.employee_id,
                        schedule_id=schedule.id,
                        attendance_date=today,
                        status=AttendanceStatus.ABSENT,
                    )
                    db.add(attendance)
                    await db.flush()

                is_leave = await check_is_leave(db, schedule.employee_id, today)
                if not is_leave:
                    alert = await create_alert(
                        db, schedule.employee_id, attendance.id,
                        AlertType.NO_CHECK_IN,
                        f"您今天{schedule.shift.name}（{schedule.shift.start_time.strftime('%H:%M')}）尚未打卡，请尽快打卡或请假"
                    )
                    results.append({
                        'employee_id': schedule.employee_id,
                        'alert_id': alert.id,
                        'message': alert.message,
                    })

                    attendance.status = AttendanceStatus.ABSENT

    await db.commit()
    return results


async def mark_alert_read(db: AsyncSession, alert_id: int, employee_id: int) -> Optional[AttendanceAlert]:
    """标记提醒为已读"""
    query = select(AttendanceAlert).where(
        and_(
            AttendanceAlert.id == alert_id,
            AttendanceAlert.employee_id == employee_id,
        )
    )
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if alert:
        alert.is_read = True
        alert.read_at = datetime.now()
        await db.commit()
        await db.refresh(alert)

    return alert


async def get_attendance_calendar(
    db: AsyncSession,
    start_date: date,
    end_date: date,
    employee_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """获取考勤日历数据"""
    query = select(Attendance).where(
        Attendance.attendance_date.between(start_date, end_date)
    )

    if employee_id:
        query = query.where(Attendance.employee_id == employee_id)

    result = await db.execute(query)
    attendances = result.scalars().all()

    emp_query = select(Employee)
    if employee_id:
        emp_query = emp_query.where(Employee.id == employee_id)
    emp_result = await db.execute(emp_query)
    employees = {e.id: e for e in emp_result.scalars().all()}

    user_query = select(User).where(User.id.in_([e.user_id for e in employees.values()]))
    user_result = await db.execute(user_query)
    users = {u.id: u for u in user_result.scalars().all()}

    schedule_query = select(Schedule).where(
        and_(
            Schedule.schedule_date.between(start_date, end_date),
        )
    )
    if employee_id:
        schedule_query = schedule_query.where(Schedule.employee_id == employee_id)
    schedule_result = await db.execute(schedule_query)
    schedules = {(s.employee_id, s.schedule_date): s for s in schedule_result.scalars().all()}

    shift_query = select(Shift)
    shift_result = await db.execute(shift_query)
    shifts = {s.id: s for s in shift_result.scalars().all()}

    leave_query = select(LeaveRequest).where(
        and_(
            LeaveRequest.status == RequestStatus.APPROVED,
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        )
    )
    if employee_id:
        leave_query = leave_query.where(LeaveRequest.employee_id == employee_id)
    leave_result = await db.execute(leave_query)
    leave_requests = leave_result.scalars().all()

    calendar_data = []
    current_date = start_date
    while current_date <= end_date:
        for emp_id, employee in employees.items():
            user = users.get(employee.user_id)
            if not user:
                continue

            attendance = next(
                (a for a in attendances if a.employee_id == emp_id and a.attendance_date == current_date),
                None
            )
            schedule = schedules.get((emp_id, current_date))
            shift = shifts.get(schedule.shift_id) if schedule else None

            is_leave = any(
                lr.employee_id == emp_id and lr.start_date <= current_date <= lr.end_date
                for lr in leave_requests
            )

            is_day_off = not schedule and current_date.weekday() in employee.unavailable_days

            item = {
                'date': current_date.isoformat(),
                'employee_id': emp_id,
                'employee_name': user.nickname or f'员工{emp_id}',
                'shift_id': shift.id if shift else None,
                'shift_name': shift.name if shift else None,
                'shift_type': shift.shift_type.value if shift else None,
                'start_time': shift.start_time.strftime('%H:%M') if shift else None,
                'end_time': shift.end_time.strftime('%H:%M') if shift else None,
                'color': shift.color if shift else None,
                'is_day_off': is_day_off,
                'is_leave': is_leave,
                'leave_type': next(
                    (lr.leave_type.value for lr in leave_requests
                     if lr.employee_id == emp_id and lr.start_date <= current_date <= lr.end_date),
                    None
                ),
                'check_in': attendance.check_in.isoformat() if attendance and attendance.check_in else None,
                'check_out': attendance.check_out.isoformat() if attendance and attendance.check_out else None,
                'status': attendance.status.value if attendance else (
                    AttendanceStatus.LEAVE.value if is_leave
                    else AttendanceStatus.DAY_OFF.value if is_day_off
                    else AttendanceStatus.ABSENT.value
                ),
            }
            calendar_data.append(item)

        current_date += timedelta(days=1)

    return calendar_data
