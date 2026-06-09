from typing import Any, Optional, List

from fastapi import APIRouter, Depends, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_admin, get_current_staff, get_current_user
from app.core.errors import NotFoundException, ConflictException, BadRequestException, ForbiddenException
from app.models import (
    ShiftPreference,
    Employee,
    User,
)
from app.schemas import (
    ApiResponse,
    ShiftPreferenceCreate,
    ShiftPreferenceUpdate,
    ShiftPreferenceResponse,
    PaginationResponse,
)
from app.services.attendance_service import get_employee_by_user_id

router = APIRouter()


@router.get("", response_model=ApiResponse[PaginationResponse[ShiftPreferenceResponse]])
async def get_preferences(
    page: int = 1,
    page_size: int = 20,
    employee_id: Optional[int] = None,
    shift_id: Optional[int] = None,
    is_recurring: Optional[bool] = None,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取班次偏好列表"""
    query = select(ShiftPreference)
    
    if employee_id:
        query = query.where(ShiftPreference.employee_id == employee_id)
    if shift_id:
        query = query.where(ShiftPreference.shift_id == shift_id)
    if is_recurring is not None:
        query = query.where(ShiftPreference.is_recurring == is_recurring)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    query = query.order_by(ShiftPreference.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    query = query.options(
        selectinload(ShiftPreference.employee).selectinload(Employee.user),
        selectinload(ShiftPreference.shift),
    )
    result = await db.execute(query)
    preferences = result.scalars().all()
    
    return ApiResponse(
        code=0,
        message="success",
        data=PaginationResponse(
            items=[ShiftPreferenceResponse.model_validate(p) for p in preferences],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        ),
    )


@router.get("/my", response_model=ApiResponse[PaginationResponse[ShiftPreferenceResponse]])
async def get_my_preferences(
    page: int = 1,
    page_size: int = 20,
    is_recurring: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取我的班次偏好"""
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee:
        raise NotFoundException(message="员工信息不存在")
    
    return await get_preferences(
        page=page,
        page_size=page_size,
        employee_id=employee.id,
        is_recurring=is_recurring,
        current_user=current_user,
        db=db,
    )


@router.get("/{preference_id}", response_model=ApiResponse[ShiftPreferenceResponse]])
async def get_preference(
    preference_id: int,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取班次偏好详情"""
    query = select(ShiftPreference).where(ShiftPreference.id == preference_id).options(
        selectinload(ShiftPreference.employee).selectinload(Employee.user),
        selectinload(ShiftPreference.shift),
    )
    result = await db.execute(query)
    preference = result.scalar_one_or_none()
    
    if not preference:
        raise NotFoundException(message="班次偏好不存在")
    
    return ApiResponse(code=0, message="success", data=ShiftPreferenceResponse.model_validate(preference))


@router.post("", response_model=ApiResponse[ShiftPreferenceResponse], status_code=status.HTTP_201_CREATED])
async def create_preference(
    preference_data: ShiftPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """提交班次偏好"""
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee:
        raise NotFoundException(message="员工信息不存在")
    
    if preference_data.preference_date is None and not preference_data.is_recurring:
        raise BadRequestException(message="请指定偏好日期或设置为重复偏好")
    
    if preference_data.is_recurring and not preference_data.recurring_days:
        raise BadRequestException(message="重复偏好需要指定重复的星期")
    
    if not preference_data.is_recurring and preference_data.recurring_days:
        raise BadRequestException(message="非重复偏好不需要指定重复的星期")
    
    existing_query = select(ShiftPreference).where(
        and_(
            ShiftPreference.employee_id == employee.id,
            ShiftPreference.shift_id == preference_data.shift_id,
        )
    )
    if preference_data.is_recurring:
        existing_query = existing_query.where(ShiftPreference.is_recurring == True)
    else:
        existing_query = existing_query.where(
            and_(
                ShiftPreference.is_recurring == False,
                ShiftPreference.preference_date == preference_data.preference_date,
            )
        )
    
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        raise ConflictException(message="该班次偏好已存在")
    
    preference = ShiftPreference(
        employee_id=employee.id,
        shift_id=preference_data.shift_id,
        preference_date=preference_data.preference_date,
        preference_level=preference_data.preference_level,
        is_recurring=preference_data.is_recurring,
        recurring_days=preference_data.recurring_days,
        remark=preference_data.remark,
    )
    
    db.add(preference)
    await db.commit()
    await db.refresh(preference)
    
    return ApiResponse(code=0, message="提交成功", data=ShiftPreferenceResponse.model_validate(preference))


@router.put("/{preference_id}", response_model=ApiResponse[ShiftPreferenceResponse]])
async def update_preference(
    preference_id: int,
    preference_data: ShiftPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """更新班次偏好"""
    query = select(ShiftPreference).where(ShiftPreference.id == preference_id)
    result = await db.execute(query)
    preference = result.scalar_one_or_none()
    
    if not preference:
        raise NotFoundException(message="班次偏好不存在")
    
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee or employee.id != preference.employee_id:
        if current_user.role != "admin":
            raise ForbiddenException(message="无权修改他人的班次偏好")
    
    update_data = preference_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preference, field, value)
    
    await db.commit()
    await db.refresh(preference)
    
    return ApiResponse(code=0, message="更新成功", data=ShiftPreferenceResponse.model_validate(preference))


@router.delete("/{preference_id}", response_model=ApiResponse[dict]])
async def delete_preference(
    preference_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """删除班次偏好"""
    query = select(ShiftPreference).where(ShiftPreference.id == preference_id)
    result = await db.execute(query)
    preference = result.scalar_one_or_none()
    
    if not preference:
        raise NotFoundException(message="班次偏好不存在")
    
    employee = await get_employee_by_user_id(db, current_user.id)
    if not employee or employee.id != preference.employee_id:
        if current_user.role != "admin":
            raise ForbiddenException(message="无权删除他人的班次偏好")
    
    await db.delete(preference)
    await db.commit()
    
    return ApiResponse(code=0, message="删除成功", data={})
