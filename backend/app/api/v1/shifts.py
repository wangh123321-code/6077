from typing import Any, Optional, List

from fastapi import APIRouter, Depends, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_admin, get_current_staff
from app.core.errors import NotFoundException, ConflictException
from app.models import Shift, User
from app.schemas import (
    ApiResponse,
    ShiftCreate,
    ShiftUpdate,
    ShiftResponse,
)

router = APIRouter()


@router.get("", response_model=ApiResponse[List[ShiftResponse]])
async def get_shifts(
    is_active: Optional[bool] = None,
    shift_type: Optional[str] = None,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取班次列表"""
    query = select(Shift).order_by(Shift.start_time)
    
    if is_active is not None:
        query = query.where(Shift.is_active == is_active)
    if shift_type:
        query = query.where(Shift.shift_type == shift_type)
    
    result = await db.execute(query)
    shifts = result.scalars().all()
    
    return ApiResponse(
        code=0,
        message="success",
        data=[ShiftResponse.model_validate(s) for s in shifts],
    )


@router.get("/{shift_id}", response_model=ApiResponse[ShiftResponse])
async def get_shift(
    shift_id: int,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取班次详情"""
    query = select(Shift).where(Shift.id == shift_id)
    result = await db.execute(query)
    shift = result.scalar_one_or_none()
    
    if not shift:
        raise NotFoundException(message="班次不存在")
    
    return ApiResponse(code=0, message="success", data=ShiftResponse.model_validate(shift))


@router.post("", response_model=ApiResponse[ShiftResponse], status_code=status.HTTP_201_CREATED)
async def create_shift(
    shift_data: ShiftCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """创建班次"""
    existing_query = select(Shift).where(Shift.name == shift_data.name)
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        raise ConflictException(message="班次名称已存在")
    
    shift = Shift(
        name=shift_data.name,
        shift_type=shift_data.shift_type,
        start_time=shift_data.start_time,
        end_time=shift_data.end_time,
        min_staff=shift_data.min_staff,
        max_staff=shift_data.max_staff,
        required_skills=shift_data.required_skills,
        color=shift_data.color,
        is_active=shift_data.is_active,
        remark=shift_data.remark,
    )
    
    db.add(shift)
    await db.commit()
    await db.refresh(shift)
    
    return ApiResponse(code=0, message="创建成功", data=ShiftResponse.model_validate(shift))


@router.put("/{shift_id}", response_model=ApiResponse[ShiftResponse])
async def update_shift(
    shift_id: int,
    shift_data: ShiftUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """更新班次"""
    query = select(Shift).where(Shift.id == shift_id)
    result = await db.execute(query)
    shift = result.scalar_one_or_none()
    
    if not shift:
        raise NotFoundException(message="班次不存在")
    
    update_data = shift_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shift, field, value)
    
    await db.commit()
    await db.refresh(shift)
    
    return ApiResponse(code=0, message="更新成功", data=ShiftResponse.model_validate(shift))


@router.delete("/{shift_id}", response_model=ApiResponse[dict])
async def delete_shift(
    shift_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """删除班次（软删除）"""
    query = select(Shift).where(Shift.id == shift_id)
    result = await db.execute(query)
    shift = result.scalar_one_or_none()
    
    if not shift:
        raise NotFoundException(message="班次不存在")
    
    shift.is_active = False
    await db.commit()
    
    return ApiResponse(code=0, message="删除成功", data={})
