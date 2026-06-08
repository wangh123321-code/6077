import math
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.core.errors import NotFoundException, ErrorCode
from app.models.service import Service, ServiceType
from app.models.user import User
from app.schemas import (
    ApiResponse,
    PaginationResponse,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)

router = APIRouter()


@router.get("", response_model=ApiResponse[PaginationResponse[ServiceResponse]])
async def get_services(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    type: Optional[ServiceType] = Query(None, description="按类型筛选"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    query = select(Service)

    if type:
        query = query.where(Service.type == type)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Service.id.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return ApiResponse(
        code=0,
        message="success",
        data=PaginationResponse(
            items=[ServiceResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get("/{service_id}", response_model=ApiResponse[ServiceResponse])
async def get_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()

    if not service:
        raise NotFoundException(
            message="服务不存在",
            code=ErrorCode.RECORD_NOT_FOUND,
        )

    return ApiResponse(
        code=0,
        message="success",
        data=ServiceResponse.model_validate(service),
    )


@router.post("", response_model=ApiResponse[ServiceResponse], status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> Any:
    new_service = Service(
        name=service_data.name,
        description=service_data.description,
        price=service_data.price,
        type=service_data.type,
        duration=service_data.duration,
        applicable_scene=service_data.applicable_scene,
    )

    db.add(new_service)
    await db.commit()
    await db.refresh(new_service)

    return ApiResponse(
        code=0,
        message="创建成功",
        data=ServiceResponse.model_validate(new_service),
    )


@router.put("/{service_id}", response_model=ApiResponse[ServiceResponse])
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> Any:
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()

    if not service:
        raise NotFoundException(
            message="服务不存在",
            code=ErrorCode.RECORD_NOT_FOUND,
        )

    update_data = service_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)

    await db.commit()
    await db.refresh(service)

    return ApiResponse(
        code=0,
        message="更新成功",
        data=ServiceResponse.model_validate(service),
    )


@router.delete("/{service_id}", response_model=ApiResponse[dict])
async def delete_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> Any:
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()

    if not service:
        raise NotFoundException(
            message="服务不存在",
            code=ErrorCode.RECORD_NOT_FOUND,
        )

    await db.delete(service)
    await db.commit()

    return ApiResponse(
        code=0,
        message="删除成功",
        data={},
    )
