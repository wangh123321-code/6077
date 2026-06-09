from typing import Any, Optional, List
from datetime import date, datetime, timedelta, time
from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_admin, get_current_staff, get_current_user
from app.core.errors import NotFoundException, ConflictException, BadRequestException, ForbiddenException
from app.models import (
    LeaveRequest,
    Employee,
    User,
    Schedule,
    RequestStatus,
    LeaveType,
)
from app.schemas import (
    ApiResponse,
    LeaveRequestCreate,
    LeaveRequestApprove,
    LeaveRequestResponse,
    PaginationResponse,
)
from app.services.attendance_service import get_employee_by_user_id

router = APIRouter()


@router.get("", response_model=ApiResponse[PaginationResponse[LeaveRequestResponse]])
async def get_leave_requests(
    page: int = 1,
    page_size: int = 10,
    status: Optional[RequestStatus] = None,
    leave_type: Optional[LeaveType] = None,
    employee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取请假申请列表"""
    query = select(LeaveRequest)
    
    if status:
        query = query.where(LeaveRequest.status == status)
    if leave_type:
        query = query.where(LeaveRequest.leave_type == leave_type)
    if employee_id:
        query = query.where(LeaveRequest.employee_id == employee_id)
    if start_date:
        query = query.where(LeaveRequest.start_date >= start_date)
    if end_date:
        query = query.where(LeaveRequest.end_date <= end_date)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    query = query.order_by(LeaveRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    leave_requests = result.scalars().all()
    
    items = []
    for lr in leave_requests:
        emp_query = select(Employee).where(Employee.id == lr.employee_id).options(selectinload(Employee.user))
        emp_result = await db.execute(emp_query)
        employee = emp_result.scalar_one_or_none()
        
        response = LeaveRequestResponse.model_validate(lr)
        if employee:
            user = employee.user
            if user:
                response.employee = {
                    "id": employee.id,
                    "user_id": user.id,
                    "employee_no": employee.employee_no,
                    "phone": user.phone,
                    "nickname": user.nickname,
                    "avatar": user.avatar,
                    "department": employee.department,
                    "position": employee.position,
                    "weekly_rest_days": employee.weekly_rest_days,
                    "max_consecutive_days": employee.max_consecutive_days,
                    "preferred_shift_type": employee.preferred_shift_type,
                    "unavailable_days": employee.unavailable_days,
                    "skills": employee.skills,
                    "is_active": employee.is_active,
                    "remark": employee.remark,
                    "created_at": employee.created_at,
                    "updated_at": employee.updated_at,
                }
        items.append(response)
    
    return ApiResponse(
        code=0,
        message="success",
        data=PaginationResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        ),
    )


@router.get("/my", response_model=ApiResponse[PaginationResponse[LeaveRequestResponse]])
async def get_my_leave_requests(
    page: int = 1,
    page_size: int = 10,
    status: Optional[RequestStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取我的请假申请"""
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee:
        raise NotFoundException(message="员工信息不存在")
    
    return await get_leave_requests(
        page=page,
        page_size=page_size,
        status=status,
        employee_id=employee.id,
        current_user=current_user,
        db=db,
    )


@router.get("/{leave_id}", response_model=ApiResponse[LeaveRequestResponse])
async def get_leave_request(
    leave_id: int,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取请假申请详情"""
    query = select(LeaveRequest).where(LeaveRequest.id == leave_id).options(
        selectinload(LeaveRequest.employee).selectinload(Employee.user)
    )
    result = await db.execute(query)
    leave_request = result.scalar_one_or_none()
    
    if not leave_request:
        raise NotFoundException(message="请假申请不存在")
    
    return ApiResponse(code=0, message="success", data=LeaveRequestResponse.model_validate(leave_request))


@router.post("", response_model=ApiResponse[LeaveRequestResponse], status_code=status.HTTP_201_CREATED)
async def create_leave_request(
    leave_data: LeaveRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """提交请假申请"""
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee:
        raise NotFoundException(message="员工信息不存在")
    
    if leave_data.end_date < leave_data.start_date:
        raise BadRequestException(message="结束日期不能早于开始日期")
    
    days = (leave_data.end_date - leave_data.start_date).days + 1
    if leave_data.start_time > leave_data.end_time and days == 1:
        raise BadRequestException(message="单日请假结束时间不能早于开始时间")
    
    existing_query = select(LeaveRequest).where(
        and_(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == RequestStatus.PENDING,
        )
    )
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        raise ConflictException(message="您有待审批的请假申请，请先处理")
    
    overlap_query = select(LeaveRequest).where(
        and_(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status.in_([RequestStatus.PENDING, RequestStatus.APPROVED]),
            LeaveRequest.start_date <= leave_data.end_date,
            LeaveRequest.end_date >= leave_data.start_date,
        )
    )
    overlap_result = await db.execute(overlap_query)
    overlap = overlap_result.scalar_one_or_none()
    
    if overlap:
        raise ConflictException(message="该时间段已有请假申请")
    
    leave_days = Decimal(str(days))
    if leave_data.start_time.time() != time(9, 0) or leave_data.end_time.time() != time(18, 0):
        start_dt = datetime.combine(leave_data.start_date, leave_data.start_time.time())
        end_dt = datetime.combine(leave_data.end_date, leave_data.end_time.time())
        hours = (end_dt - start_dt).total_seconds() / 3600
        leave_days = Decimal(str(round(hours / 8, 1)))
    
    leave_request = LeaveRequest(
        employee_id=employee.id,
        leave_type=leave_data.leave_type,
        start_date=leave_data.start_date,
        end_date=leave_data.end_date,
        start_time=leave_data.start_time.time(),
        end_time=leave_data.end_time.time(),
        days=leave_days,
        reason=leave_data.reason,
    )
    
    db.add(leave_request)
    await db.commit()
    await db.refresh(leave_request)
    
    return ApiResponse(code=0, message="提交成功", data=LeaveRequestResponse.model_validate(leave_request))


@router.put("/{leave_id}/approve", response_model=ApiResponse[LeaveRequestResponse])
async def approve_leave_request(
    leave_id: int,
    approve_data: LeaveRequestApprove,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """审批请假申请"""
    query = select(LeaveRequest).where(LeaveRequest.id == leave_id)
    result = await db.execute(query)
    leave_request = result.scalar_one_or_none()
    
    if not leave_request:
        raise NotFoundException(message="请假申请不存在")
    
    if leave_request.status != RequestStatus.PENDING:
        raise ConflictException(message="该申请已处理，无法重复审批")
    
    leave_request.status = approve_data.status
    leave_request.approver_id = current_user.id
    leave_request.approval_comment = approve_data.approval_comment
    leave_request.approved_at = datetime.now()
    
    if approve_data.status == RequestStatus.APPROVED:
        schedule_query = select(Schedule).where(
            and_(
                Schedule.employee_id == leave_request.employee_id,
                Schedule.schedule_date.between(leave_request.start_date, leave_request.end_date),
            )
        )
        schedule_result = await db.execute(schedule_query)
        schedules = schedule_result.scalars().all()
        
        for schedule in schedules:
            await db.delete(schedule)
    
    await db.commit()
    await db.refresh(leave_request)
    
    return ApiResponse(code=0, message="审批成功", data=LeaveRequestResponse.model_validate(leave_request))


@router.delete("/{leave_id}", response_model=ApiResponse[dict])
async def cancel_leave_request(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """撤销请假申请"""
    query = select(LeaveRequest).where(LeaveRequest.id == leave_id)
    result = await db.execute(query)
    leave_request = result.scalar_one_or_none()
    
    if not leave_request:
        raise NotFoundException(message="请假申请不存在")
    
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee or employee.id != leave_request.employee_id:
        if current_user.role != "admin":
            raise ForbiddenException(message="无权撤销他人的请假申请")
    
    if leave_request.status not in [RequestStatus.PENDING, RequestStatus.APPROVED]:
        raise ConflictException(message="该申请状态不允许撤销")
    
    if leave_request.status == RequestStatus.APPROVED and leave_request.start_date <= date.today():
        raise ConflictException(message="已生效的请假不能撤销")
    
    leave_request.status = RequestStatus.CANCELLED
    await db.commit()
    
    return ApiResponse(code=0, message="撤销成功", data={})
