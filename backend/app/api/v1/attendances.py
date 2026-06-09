from typing import Any, Optional, List, Dict
from datetime import date, datetime
from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_admin, get_current_staff, get_current_user
from app.core.errors import NotFoundException, ConflictException, BadRequestException
from app.models import (
    Attendance,
    AttendanceAlert,
    Employee,
    User,
    AttendanceStatus,
    Schedule,
    Shift,
)
from app.schemas import (
    ApiResponse,
    AttendanceCheckInRequest,
    AttendanceCheckOutRequest,
    AttendanceResponse,
    AttendanceAlertResponse,
    AttendanceReportRequest,
    AttendanceReportResponse,
    AttendanceReportItem,
    PaginationResponse,
)
from app.services.attendance_service import (
    employee_check_in,
    employee_check_out,
    get_employee_by_user_id,
    mark_alert_read,
    get_attendance_calendar,
)
from app.services.scheduling_service import calculate_attendance_stats

router = APIRouter()


@router.post("/check-in", response_model=ApiResponse[AttendanceResponse])
async def check_in(
    check_in_data: AttendanceCheckInRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """上班打卡"""
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee:
        raise NotFoundException(message="员工信息不存在")
    
    try:
        attendance = await employee_check_in(
            db,
            employee.id,
            check_in_data.check_in_time,
            check_in_data.location,
        )
    except ValueError as e:
        raise ConflictException(message=str(e))
    
    return ApiResponse(code=0, message="打卡成功", data=AttendanceResponse.model_validate(attendance))


@router.post("/check-out", response_model=ApiResponse[AttendanceResponse])
async def check_out(
    check_out_data: AttendanceCheckOutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """下班打卡"""
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee:
        raise NotFoundException(message="员工信息不存在")
    
    try:
        attendance = await employee_check_out(
            db,
            employee.id,
            check_out_data.check_out_time,
            check_out_data.location,
        )
    except ValueError as e:
        raise ConflictException(message=str(e))
    
    return ApiResponse(code=0, message="打卡成功", data=AttendanceResponse.model_validate(attendance))


@router.get("/today", response_model=ApiResponse[AttendanceResponse])
async def get_today_attendance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取今日考勤"""
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee:
        raise NotFoundException(message="员工信息不存在")
    
    today = date.today()
    query = select(Attendance).where(
        and_(
            Attendance.employee_id == employee.id,
            Attendance.attendance_date == today,
        )
    ).options(
        selectinload(Attendance.schedule).selectinload(Schedule.shift)
    )
    result = await db.execute(query)
    attendance = result.scalar_one_or_none()
    
    if not attendance:
        from app.services.attendance_service import get_or_create_attendance
        attendance = await get_or_create_attendance(db, employee.id, today)
        await db.commit()
    
    return ApiResponse(code=0, message="success", data=AttendanceResponse.model_validate(attendance))


@router.get("/calendar", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_calendar(
    start_date: date,
    end_date: date,
    employee_id: Optional[int] = None,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取考勤日历"""
    if not employee_id:
        employee = await get_employee_by_user_id(db, current_user.id)
        if employee:
            employee_id = employee.id
    
    if end_date < start_date:
        raise BadRequestException(message="结束日期不能早于开始日期")
    
    if (end_date - start_date).days > 60:
        raise BadRequestException(message="查询范围不能超过60天")
    
    data = await get_attendance_calendar(db, start_date, end_date, employee_id)
    
    return ApiResponse(code=0, message="success", data=data)


@router.get("/alerts", response_model=ApiResponse[PaginationResponse[AttendanceAlertResponse]])
async def get_alerts(
    page: int = 1,
    page_size: int = 20,
    is_read: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取我的考勤提醒"""
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee:
        raise NotFoundException(message="员工信息不存在")
    
    query = select(AttendanceAlert).where(AttendanceAlert.employee_id == employee.id)
    
    if is_read is not None:
        query = query.where(AttendanceAlert.is_read == is_read)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    query = query.order_by(AttendanceAlert.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return ApiResponse(
        code=0,
        message="success",
        data=PaginationResponse(
            items=[AttendanceAlertResponse.model_validate(a) for a in alerts],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        ),
    )


@router.post("/alerts/{alert_id}/read", response_model=ApiResponse[dict])
async def mark_alert_as_read(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """标记提醒为已读"""
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee:
        raise NotFoundException(message="员工信息不存在")
    
    alert = await mark_alert_read(db, alert_id, employee.id)
    if not alert:
        raise NotFoundException(message="提醒不存在或无权限")
    
    return ApiResponse(code=0, message="标记成功", data={})


@router.get("/report", response_model=ApiResponse[AttendanceReportResponse])
async def get_attendance_report(
    start_date: date,
    end_date: date,
    employee_id: Optional[int] = None,
    department: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取考勤报表"""
    if end_date < start_date:
        raise BadRequestException(message="结束日期不能早于开始日期")
    
    if (end_date - start_date).days > 366:
        raise BadRequestException(message="查询范围不能超过366天")
    
    stats = await calculate_attendance_stats(db, start_date, end_date, employee_id)
    
    if department:
        emp_query = select(Employee).where(Employee.department == department)
        emp_result = await db.execute(emp_query)
        dept_emp_ids = [e.id for e in emp_result.scalars().all()]
        stats = [s for s in stats if s['employee_id'] in dept_emp_ids]
    
    total_work_days = sum(s['total_work_days'] for s in stats)
    total_work_hours = sum(s['total_work_hours'] for s in stats)
    total_overtime_hours = sum(s['total_overtime_hours'] for s in stats)
    total_late_count = sum(s['late_count'] for s in stats)
    total_early_leave_count = sum(s['early_leave_count'] for s in stats)
    total_absent_count = sum(s['absent_count'] for s in stats)
    total_leave_days = sum(s['leave_days'] for s in stats)
    
    leave_type_totals: Dict[str, float] = defaultdict(float)
    for s in stats:
        for leave_type, days in s['leave_type_counts'].items():
            leave_type_totals[leave_type] += days
    
    items = [AttendanceReportItem(**s) for s in stats]
    
    return ApiResponse(
        code=0,
        message="success",
        data=AttendanceReportResponse(
            start_date=start_date,
            end_date=end_date,
            total_employees=len(items),
            items=items,
            summary={
                'total_work_days': total_work_days,
                'total_work_hours': total_work_hours,
                'total_overtime_hours': total_overtime_hours,
                'total_late_count': total_late_count,
                'total_early_leave_count': total_early_leave_count,
                'total_absent_count': total_absent_count,
                'total_leave_days': total_leave_days,
                'leave_type_totals': dict(leave_type_totals),
                'avg_attendance_rate': round(
                    (total_work_days / max(total_work_days + total_absent_count + float(total_leave_days), 1)) * 100,
                    2
                ) if items else 0,
            },
        ),
    )


@router.get("/my-report", response_model=ApiResponse[AttendanceReportResponse])
async def get_my_attendance_report(
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取我的考勤报表"""
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee:
        raise NotFoundException(message="员工信息不存在")
    
    return await get_attendance_report(
        start_date=start_date,
        end_date=end_date,
        employee_id=employee.id,
        current_user=current_user,
        db=db,
    )


@router.get("", response_model=ApiResponse[PaginationResponse[AttendanceResponse]])
async def get_attendances(
    page: int = 1,
    page_size: int = 20,
    employee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[AttendanceStatus] = None,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取考勤记录列表"""
    query = select(Attendance)
    
    if employee_id:
        query = query.where(Attendance.employee_id == employee_id)
    if start_date:
        query = query.where(Attendance.attendance_date >= start_date)
    if end_date:
        query = query.where(Attendance.attendance_date <= end_date)
    if status:
        query = query.where(Attendance.status == status)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    query = query.order_by(Attendance.attendance_date.desc(), Attendance.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.options(
        selectinload(Attendance.employee).selectinload(Employee.user),
        selectinload(Attendance.schedule).selectinload(Schedule.shift),
    )
    result = await db.execute(query)
    attendances = result.scalars().all()
    
    return ApiResponse(
        code=0,
        message="success",
        data=PaginationResponse(
            items=[AttendanceResponse.model_validate(a) for a in attendances],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        ),
    )


@router.get("/{attendance_id}", response_model=ApiResponse[AttendanceResponse])
async def get_attendance(
    attendance_id: int,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取考勤详情"""
    query = select(Attendance).where(Attendance.id == attendance_id).options(
        selectinload(Attendance.employee).selectinload(Employee.user),
        selectinload(Attendance.schedule).selectinload(Schedule.shift),
    )
    result = await db.execute(query)
    attendance = result.scalar_one_or_none()
    
    if not attendance:
        raise NotFoundException(message="考勤记录不存在")
    
    return ApiResponse(code=0, message="success", data=AttendanceResponse.model_validate(attendance))


@router.put("/{attendance_id}", response_model=ApiResponse[AttendanceResponse])
async def update_attendance(
    attendance_id: int,
    attendance_data: dict,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """手动修正考勤记录"""
    query = select(Attendance).where(Attendance.id == attendance_id)
    result = await db.execute(query)
    attendance = result.scalar_one_or_none()
    
    if not attendance:
        raise NotFoundException(message="考勤记录不存在")
    
    allowed_fields = ['check_in', 'check_out', 'status', 'work_hours', 'overtime_hours', 
                      'late_minutes', 'early_leave_minutes', 'remark']
    
    for field, value in attendance_data.items():
        if field in allowed_fields:
            if field in ['check_in', 'check_out'] and isinstance(value, str):
                value = datetime.fromisoformat(value)
            setattr(attendance, field, value)
    
    attendance.remark = f"{attendance.remark or ''} (管理员修正)".strip()
    
    await db.commit()
    await db.refresh(attendance)
    
    return ApiResponse(code=0, message="修正成功", data=AttendanceResponse.model_validate(attendance))
