from typing import Any, Optional, List, Dict
from datetime import date, datetime, timedelta
from collections import defaultdict

from fastapi import APIRouter, Depends, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_admin, get_current_staff, get_current_user
from app.core.errors import NotFoundException, ConflictException, BadRequestException
from app.models import (
    Schedule,
    Shift,
    Employee,
    SchedulingRule,
    LeaveRequest,
    User,
    ShiftType,
)
from app.schemas import (
    ApiResponse,
    ScheduleCreateRequest,
    ScheduleUpdateRequest,
    ScheduleSwapRequest,
    ScheduleResponse,
    ScheduleGenerateRequest,
    ScheduleConflictCheckRequest,
    ScheduleConflictResponse,
    ScheduleCalendarRequest,
    ScheduleCalendarResponse,
    ScheduleCalendarItem,
    ShiftResponse,
)
from app.services.scheduling_service import SchedulingAlgorithm, check_schedule_conflict

router = APIRouter()


@router.get("/calendar", response_model=ApiResponse[ScheduleCalendarResponse])
async def get_schedule_calendar(
    start_date: date,
    end_date: date,
    employee_id: Optional[int] = None,
    department: Optional[str] = None,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取排班日历"""
    if end_date < start_date:
        raise BadRequestException(message="结束日期不能早于开始日期")
    
    if (end_date - start_date).days > 60:
        raise BadRequestException(message="查询范围不能超过60天")
    
    emp_query = select(Employee).where(Employee.is_active == True)
    if employee_id:
        emp_query = emp_query.where(Employee.id == employee_id)
    if department:
        emp_query = emp_query.where(Employee.department == department)
    emp_result = await db.execute(emp_query)
    employees = {e.id: e for e in emp_result.scalars().all()}
    
    user_query = select(User).where(User.id.in_([e.user_id for e in employees.values()]))
    user_result = await db.execute(user_query)
    users = {u.id: u for u in user_result.scalars().all()}
    
    schedule_query = select(Schedule).where(
        and_(
            Schedule.schedule_date.between(start_date, end_date),
            Schedule.employee_id.in_(list(employees.keys())),
        )
    ).options(selectinload(Schedule.shift))
    schedule_result = await db.execute(schedule_query)
    schedules = schedule_result.scalars().all()
    
    leave_query = select(LeaveRequest).where(
        and_(
            LeaveRequest.status == "approved",
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
            LeaveRequest.employee_id.in_(list(employees.keys())),
        )
    )
    leave_result = await db.execute(leave_query)
    leave_requests = leave_result.scalars().all()
    
    shift_query = select(Shift).where(Shift.is_active == True)
    shift_result = await db.execute(shift_query)
    shifts = {s.id: s for s in shift_result.scalars().all()}
    
    schedule_map = defaultdict(lambda: defaultdict(dict))
    for s in schedules:
        schedule_map[s.schedule_date][s.employee_id] = s
    
    leave_map = defaultdict(list)
    for lr in leave_requests:
        current = lr.start_date
        while current <= lr.end_date:
            leave_map[(lr.employee_id, current)].append(lr)
            current += timedelta(days=1)
    
    items = []
    current = start_date
    while current <= end_date:
        for emp_id, emp in employees.items():
            user = users.get(emp.user_id)
            if not user:
                continue
            
            schedule = schedule_map.get(current, {}).get(emp_id)
            shift = shifts.get(schedule.shift_id) if schedule else None
            
            is_leave = (emp_id, current) in leave_map
            leave_type = leave_map[(emp_id, current)][0].leave_type if is_leave else None
            
            is_day_off = not schedule and current.weekday() in emp.unavailable_days
            
            item = ScheduleCalendarItem(
                date=current,
                employee_id=emp_id,
                employee_name=user.nickname or f"员工{emp_id}",
                shift_id=shift.id if shift else None,
                shift_name=shift.name if shift else None,
                shift_type=shift.shift_type if shift else None,
                start_time=shift.start_time if shift else None,
                end_time=shift.end_time if shift else None,
                color=shift.color if shift else None,
                is_day_off=is_day_off,
                is_leave=is_leave,
                leave_type=leave_type,
            )
            items.append(item)
        
        current += timedelta(days=1)
    
    shift_info = [ShiftResponse.model_validate(s) for s in shifts.values()]
    
    return ApiResponse(
        code=0,
        message="success",
        data=ScheduleCalendarResponse(
            start_date=start_date,
            end_date=end_date,
            items=items,
            shift_info=shift_info,
        ),
    )


@router.get("/{schedule_id}", response_model=ApiResponse[ScheduleResponse])
async def get_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取排班详情"""
    query = select(Schedule).where(Schedule.id == schedule_id).options(
        selectinload(Schedule.employee),
        selectinload(Schedule.shift),
    )
    result = await db.execute(query)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise NotFoundException(message="排班记录不存在")
    
    return ApiResponse(code=0, message="success", data=ScheduleResponse.model_validate(schedule))


@router.post("", response_model=ApiResponse[ScheduleResponse], status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """创建单条排班"""
    has_conflict, conflicts = await check_schedule_conflict(
        db,
        schedule_data.employee_id,
        schedule_data.shift_id,
        schedule_data.schedule_date,
    )
    
    if has_conflict:
        raise ConflictException(
            message=f"排班冲突: {'; '.join([c['message'] for c in conflicts])}",
            data={"conflicts": conflicts},
        )
    
    schedule = Schedule(
        employee_id=schedule_data.employee_id,
        shift_id=schedule_data.shift_id,
        schedule_date=schedule_data.schedule_date,
        is_confirmed=schedule_data.is_confirmed,
        remark=schedule_data.remark,
    )
    
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    
    return ApiResponse(code=0, message="创建成功", data=ScheduleResponse.model_validate(schedule))


@router.post("/check-conflict", response_model=ApiResponse[ScheduleConflictResponse])
async def check_conflict(
    check_data: ScheduleConflictCheckRequest,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """检查排班冲突"""
    has_conflict, conflicts = await check_schedule_conflict(
        db,
        check_data.employee_id,
        check_data.shift_id,
        check_data.schedule_date,
        check_data.exclude_schedule_id,
    )
    
    return ApiResponse(
        code=0,
        message="success",
        data=ScheduleConflictResponse(
            has_conflict=has_conflict,
            conflicts=conflicts,
            message="存在冲突" if has_conflict else "无冲突",
        ),
    )


@router.post("/generate", response_model=ApiResponse[Dict[str, Any]])
async def generate_schedules(
    generate_data: ScheduleGenerateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """智能生成排班"""
    if generate_data.end_date < generate_data.start_date:
        raise BadRequestException(message="结束日期不能早于开始日期")
    
    if (generate_data.end_date - generate_data.start_date).days > 31:
        raise BadRequestException(message="排班范围不能超过31天")
    
    rule_id = generate_data.rule_id
    if not rule_id:
        rule_query = select(SchedulingRule).where(
            (SchedulingRule.is_default == True) &
            (SchedulingRule.is_active == True)
        )
        rule_result = await db.execute(rule_query)
        rule = rule_result.scalar_one_or_none()
        if not rule:
            rule_query = select(SchedulingRule).where(SchedulingRule.is_active == True).limit(1)
            rule_result = await db.execute(rule_query)
            rule = rule_result.scalar_one_or_none()
    else:
        rule_query = select(SchedulingRule).where(SchedulingRule.id == rule_id)
        rule_result = await db.execute(rule_query)
        rule = rule_result.scalar_one_or_none()
    
    if not rule:
        raise NotFoundException(message="未找到有效的排班规则")
    
    algorithm = SchedulingAlgorithm(db, rule)
    await algorithm.initialize(
        generate_data.start_date,
        generate_data.end_date,
        generate_data.employee_ids,
    )
    
    generated_schedules, warnings = await algorithm.generate(
        generate_data.start_date,
        generate_data.end_date,
    )
    
    for schedule in generated_schedules:
        db.add(schedule)
    
    await db.commit()
    
    for schedule in generated_schedules:
        await db.refresh(schedule)
    
    return ApiResponse(
        code=0,
        message="success",
        data={
            "generated_count": len(generated_schedules),
            "warnings": warnings,
            "schedules": [ScheduleResponse.model_validate(s) for s in generated_schedules],
        },
    )


@router.put("/{schedule_id}", response_model=ApiResponse[ScheduleResponse])
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """更新排班"""
    query = select(Schedule).where(Schedule.id == schedule_id)
    result = await db.execute(query)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise NotFoundException(message="排班记录不存在")
    
    if schedule_data.shift_id is not None:
        has_conflict, conflicts = await check_schedule_conflict(
            db,
            schedule.employee_id,
            schedule_data.shift_id,
            schedule.schedule_date,
            schedule.id,
        )
        
        if has_conflict:
            raise ConflictException(
                message=f"排班冲突: {'; '.join([c['message'] for c in conflicts])}",
                data={"conflicts": conflicts},
            )
    
    update_data = schedule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    await db.commit()
    await db.refresh(schedule)
    
    return ApiResponse(code=0, message="更新成功", data=ScheduleResponse.model_validate(schedule))


@router.post("/swap", response_model=ApiResponse[Dict[str, Any]])
async def swap_schedule(
    swap_data: ScheduleSwapRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """调班（拖拽换班）"""
    from_query = select(Schedule).where(
        and_(
            Schedule.employee_id == swap_data.from_employee_id,
            Schedule.schedule_date == swap_data.schedule_date,
            Schedule.shift_id == swap_data.shift_id,
        )
    )
    from_result = await db.execute(from_query)
    from_schedule = from_result.scalar_one_or_none()
    
    if not from_schedule:
        raise NotFoundException(message="原排班记录不存在")
    
    to_has_conflict, to_conflicts = await check_schedule_conflict(
        db,
        swap_data.to_employee_id,
        swap_data.shift_id,
        swap_data.schedule_date,
        from_schedule.id,
    )
    
    if to_has_conflict:
        raise ConflictException(
            message=f"目标员工排班冲突: {'; '.join([c['message'] for c in to_conflicts])}",
            data={"conflicts": to_conflicts},
        )
    
    from_schedule.employee_id = swap_data.to_employee_id
    from_schedule.is_swapped = True
    from_schedule.original_employee_id = swap_data.from_employee_id
    from_schedule.remark = f"{swap_data.reason or '调班'}: 由员工{swap_data.from_employee_id}调整为员工{swap_data.to_employee_id}"
    
    await db.commit()
    await db.refresh(from_schedule)
    
    return ApiResponse(
        code=0,
        message="调班成功",
        data={
            "schedule": ScheduleResponse.model_validate(from_schedule),
        },
    )


@router.delete("/{schedule_id}", response_model=ApiResponse[dict])
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """删除排班"""
    query = select(Schedule).where(Schedule.id == schedule_id)
    result = await db.execute(query)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise NotFoundException(message="排班记录不存在")
    
    await db.delete(schedule)
    await db.commit()
    
    return ApiResponse(code=0, message="删除成功", data={})


@router.post("/{schedule_id}/confirm", response_model=ApiResponse[ScheduleResponse])
async def confirm_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """确认排班"""
    query = select(Schedule).where(Schedule.id == schedule_id)
    result = await db.execute(query)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise NotFoundException(message="排班记录不存在")
    
    schedule.is_confirmed = True
    await db.commit()
    await db.refresh(schedule)
    
    return ApiResponse(code=0, message="确认成功", data=ScheduleResponse.model_validate(schedule))
