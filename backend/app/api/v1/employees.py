from typing import Any, Optional, List
from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_admin, get_current_staff
from app.core.errors import NotFoundException, ConflictException
from app.models import Employee, User, UserRole
from app.schemas import (
    ApiResponse,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListItem,
    PaginationRequest,
    PaginationResponse,
)

router = APIRouter()


@router.get("", response_model=ApiResponse[PaginationResponse[EmployeeListItem]])
async def get_employees(
    page: int = 1,
    page_size: int = 10,
    department: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取员工列表"""
    query = select(Employee)
    
    if department:
        query = query.where(Employee.department == department)
    if is_active is not None:
        query = query.where(Employee.is_active == is_active)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    employees = result.scalars().all()
    
    items = []
    for emp in employees:
        user_query = select(User).where(User.id == emp.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        item = EmployeeListItem.model_validate(emp)
        if user:
            item.user = {
                "id": user.id,
                "phone": user.phone,
                "nickname": user.nickname,
                "avatar": user.avatar,
            }
        items.append(item)
    
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


@router.get("/{employee_id}", response_model=ApiResponse[EmployeeResponse])
async def get_employee(
    employee_id: int,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取员工详情"""
    query = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(query)
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise NotFoundException(message="员工不存在")
    
    user_query = select(User).where(User.id == employee.user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    response = EmployeeResponse.model_validate(employee)
    if user:
        response.user = {
            "id": user.id,
            "phone": user.phone,
            "nickname": user.nickname,
            "avatar": user.avatar,
        }
    
    return ApiResponse(code=0, message="success", data=response)


@router.post("", response_model=ApiResponse[EmployeeResponse], status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """创建员工"""
    user_query = select(User).where(User.id == employee_data.user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise NotFoundException(message="用户不存在")
    
    existing_query = select(Employee).where(
        (Employee.user_id == employee_data.user_id) |
        (Employee.employee_no == employee_data.employee_no)
    )
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        raise ConflictException(message="该用户已创建员工信息或员工编号已存在")
    
    if user.role not in [UserRole.STAFF, UserRole.ADMIN]:
        user.role = UserRole.STAFF
        await db.commit()
    
    employee = Employee(
        user_id=employee_data.user_id,
        employee_no=employee_data.employee_no,
        department=employee_data.department,
        position=employee_data.position,
        hire_date=employee_data.hire_date,
        weekly_rest_days=employee_data.weekly_rest_days,
        max_consecutive_days=employee_data.max_consecutive_days,
        preferred_shift_type=employee_data.preferred_shift_type,
        unavailable_days=employee_data.unavailable_days,
        skills=employee_data.skills,
        is_active=employee_data.is_active,
        remark=employee_data.remark,
    )
    
    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    
    response = EmployeeResponse.model_validate(employee)
    response.user = {
        "id": user.id,
        "phone": user.phone,
        "nickname": user.nickname,
        "avatar": user.avatar,
    }
    
    return ApiResponse(code=0, message="创建成功", data=response)


@router.put("/{employee_id}", response_model=ApiResponse[EmployeeResponse])
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """更新员工信息"""
    query = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(query)
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise NotFoundException(message="员工不存在")
    
    update_data = employee_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)
    
    await db.commit()
    await db.refresh(employee)
    
    user_query = select(User).where(User.id == employee.user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    response = EmployeeResponse.model_validate(employee)
    if user:
        response.user = {
            "id": user.id,
            "phone": user.phone,
            "nickname": user.nickname,
            "avatar": user.avatar,
        }
    
    return ApiResponse(code=0, message="更新成功", data=response)


@router.delete("/{employee_id}", response_model=ApiResponse[dict])
async def delete_employee(
    employee_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """删除员工（软删除）"""
    query = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(query)
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise NotFoundException(message="员工不存在")
    
    employee.is_active = False
    await db.commit()
    
    return ApiResponse(code=0, message="删除成功", data={})
