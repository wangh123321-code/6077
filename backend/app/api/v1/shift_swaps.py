from typing import Any, Optional, List
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_admin, get_current_staff, get_current_user
from app.core.errors import NotFoundException, ConflictException, BadRequestException, ForbiddenException
from app.models import (
    ShiftSwap,
    Employee,
    User,
    RequestStatus,
)
from app.schemas import (
    ApiResponse,
    ShiftSwapCreate,
    ShiftSwapApprove,
    ShiftSwapResponse,
    PaginationResponse,
)
from app.services.attendance_service import get_employee_by_user_id
from app.services.scheduling_service import check_schedule_conflict

router = APIRouter()


@router.get("", response_model=ApiResponse[PaginationResponse[ShiftSwapResponse]])
async def get_shift_swaps(
    page: int = 1,
    page_size: int = 10,
    status: Optional[RequestStatus] = None,
    employee_id: Optional[int] = None,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取调班申请列表"""
    query = select(ShiftSwap)
    
    if status:
        query = query.where(ShiftSwap.status == status)
    if employee_id:
        query = query.where(
            (ShiftSwap.employee_id == employee_id) |
            (ShiftSwap.target_employee_id == employee_id)
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    query = query.order_by(ShiftSwap.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    query = query.options(
        selectinload(ShiftSwap.employee).selectinload(Employee.user),
        selectinload(ShiftSwap.target_employee).selectinload(Employee.user),
        selectinload(ShiftSwap.request_shift),
        selectinload(ShiftSwap.target_shift),
    )
    result = await db.execute(query)
    shift_swaps = result.scalars().all()
    
    return ApiResponse(
        code=0,
        message="success",
        data=PaginationResponse(
            items=[ShiftSwapResponse.model_validate(ss) for ss in shift_swaps],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        ),
    )


@router.get("/my", response_model=ApiResponse[PaginationResponse[ShiftSwapResponse]])
async def get_my_shift_swaps(
    page: int = 1,
    page_size: int = 10,
    status: Optional[RequestStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取我的调班申请"""
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee:
        raise NotFoundException(message="员工信息不存在")
    
    return await get_shift_swaps(
        page=page,
        page_size=page_size,
        status=status,
        employee_id=employee.id,
        current_user=current_user,
        db=db,
    )


@router.get("/{swap_id}", response_model=ApiResponse[ShiftSwapResponse])
async def get_shift_swap(
    swap_id: int,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取调班申请详情"""
    query = select(ShiftSwap).where(ShiftSwap.id == swap_id).options(
        selectinload(ShiftSwap.employee).selectinload(Employee.user),
        selectinload(ShiftSwap.target_employee).selectinload(Employee.user),
        selectinload(ShiftSwap.request_shift),
        selectinload(ShiftSwap.target_shift),
    )
    result = await db.execute(query)
    shift_swap = result.scalar_one_or_none()
    
    if not shift_swap:
        raise NotFoundException(message="调班申请不存在")
    
    return ApiResponse(code=0, message="success", data=ShiftSwapResponse.model_validate(shift_swap))


@router.post("", response_model=ApiResponse[ShiftSwapResponse], status_code=status.HTTP_201_CREATED)
async def create_shift_swap(
    swap_data: ShiftSwapCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """提交调班申请"""
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee:
        raise NotFoundException(message="员工信息不存在")
    
    if swap_data.employee_id != employee.id:
        if current_user.role != "admin":
            raise ForbiddenException(message="无权替他人提交调班申请")
    
    if swap_data.employee_id == swap_data.target_employee_id:
        raise BadRequestException(message="不能和自己调班")
    
    existing_query = select(ShiftSwap).where(
        and_(
            ShiftSwap.employee_id == swap_data.employee_id,
            ShiftSwap.status == RequestStatus.PENDING,
        )
    )
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        raise ConflictException(message="您有待审批的调班申请，请先处理")
    
    emp_has_conflict, emp_conflicts = await check_schedule_conflict(
        db,
        swap_data.employee_id,
        swap_data.target_shift_id,
        swap_data.target_date,
    )
    
    if emp_has_conflict:
        raise ConflictException(
            message=f"您在目标日期已有排班: {'; '.join([c['message'] for c in emp_conflicts])}",
        )
    
    target_has_conflict, target_conflicts = await check_schedule_conflict(
        db,
        swap_data.target_employee_id,
        swap_data.request_shift_id,
        swap_data.request_date,
    )
    
    if target_has_conflict:
        raise ConflictException(
            message=f"对方在目标日期已有排班: {'; '.join([c['message'] for c in target_conflicts])}",
        )
    
    shift_swap = ShiftSwap(
        employee_id=swap_data.employee_id,
        target_employee_id=swap_data.target_employee_id,
        request_date=swap_data.request_date,
        target_date=swap_data.target_date,
        request_shift_id=swap_data.request_shift_id,
        target_shift_id=swap_data.target_shift_id,
        reason=swap_data.reason,
    )
    
    db.add(shift_swap)
    await db.commit()
    await db.refresh(shift_swap)
    
    return ApiResponse(code=0, message="提交成功", data=ShiftSwapResponse.model_validate(shift_swap))


@router.put("/{swap_id}/approve", response_model=ApiResponse[ShiftSwapResponse])
async def approve_shift_swap(
    swap_id: int,
    approve_data: ShiftSwapApprove,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """审批调班申请"""
    query = select(ShiftSwap).where(ShiftSwap.id == swap_id)
    result = await db.execute(query)
    shift_swap = result.scalar_one_or_none()
    
    if not shift_swap:
        raise NotFoundException(message="调班申请不存在")
    
    if shift_swap.status != RequestStatus.PENDING:
        raise ConflictException(message="该申请已处理，无法重复审批")
    
    shift_swap.status = approve_data.status
    shift_swap.approver_id = current_user.id
    shift_swap.approval_comment = approve_data.approval_comment
    shift_swap.approved_at = datetime.now()
    
    if approve_data.status == RequestStatus.APPROVED:
        from app.models import Schedule
        
        emp_schedule_query = select(Schedule).where(
            and_(
                Schedule.employee_id == shift_swap.employee_id,
                Schedule.schedule_date == shift_swap.request_date,
                Schedule.shift_id == shift_swap.request_shift_id,
            )
        )
        emp_schedule_result = await db.execute(emp_schedule_query)
        emp_schedule = emp_schedule_result.scalar_one_or_none()
        
        target_schedule_query = select(Schedule).where(
            and_(
                Schedule.employee_id == shift_swap.target_employee_id,
                Schedule.schedule_date == shift_swap.target_date,
                Schedule.shift_id == shift_swap.target_shift_id,
            )
        )
        target_schedule_result = await db.execute(target_schedule_query)
        target_schedule = target_schedule_result.scalar_one_or_none()
        
        if emp_schedule:
            emp_schedule.employee_id = shift_swap.target_employee_id
            emp_schedule.is_swapped = True
            emp_schedule.original_employee_id = shift_swap.employee_id
            emp_schedule.remark = f"调班: 由员工{shift_swap.employee_id}调整为员工{shift_swap.target_employee_id}"
        
        if target_schedule:
            target_schedule.employee_id = shift_swap.employee_id
            target_schedule.is_swapped = True
            target_schedule.original_employee_id = shift_swap.target_employee_id
            target_schedule.remark = f"调班: 由员工{shift_swap.target_employee_id}调整为员工{shift_swap.employee_id}"
    
    await db.commit()
    await db.refresh(shift_swap)
    
    return ApiResponse(code=0, message="审批成功", data=ShiftSwapResponse.model_validate(shift_swap))


@router.delete("/{swap_id}", response_model=ApiResponse[dict])
async def cancel_shift_swap(
    swap_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """撤销调班申请"""
    query = select(ShiftSwap).where(ShiftSwap.id == swap_id)
    result = await db.execute(query)
    shift_swap = result.scalar_one_or_none()
    
    if not shift_swap:
        raise NotFoundException(message="调班申请不存在")
    
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee or employee.id not in [shift_swap.employee_id, shift_swap.target_employee_id]:
        if current_user.role != "admin":
            raise ForbiddenException(message="无权撤销他人的调班申请")
    
    if shift_swap.status not in [RequestStatus.PENDING]:
        raise ConflictException(message="该申请状态不允许撤销")
    
    shift_swap.status = RequestStatus.CANCELLED
    await db.commit()
    
    return ApiResponse(code=0, message="撤销成功", data={})
