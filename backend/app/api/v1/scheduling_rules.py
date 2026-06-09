from typing import Any, Optional, List

from fastapi import APIRouter, Depends, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_admin, get_current_staff
from app.core.errors import NotFoundException, ConflictException
from app.models import SchedulingRule, User
from app.schemas import (
    ApiResponse,
    SchedulingRuleCreate,
    SchedulingRuleUpdate,
    SchedulingRuleResponse,
)

router = APIRouter()


@router.get("", response_model=ApiResponse[List[SchedulingRuleResponse]])
async def get_scheduling_rules(
    is_active: Optional[bool] = None,
    is_default: Optional[bool] = None,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取排班规则列表"""
    query = select(SchedulingRule)
    
    if is_active is not None:
        query = query.where(SchedulingRule.is_active == is_active)
    if is_default is not None:
        query = query.where(SchedulingRule.is_default == is_default)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return ApiResponse(
        code=0,
        message="success",
        data=[SchedulingRuleResponse.model_validate(r) for r in rules],
    )


@router.get("/default", response_model=ApiResponse[SchedulingRuleResponse])
async def get_default_rule(
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取默认排班规则"""
    query = select(SchedulingRule).where(
        (SchedulingRule.is_default == True) &
        (SchedulingRule.is_active == True)
    )
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        query = select(SchedulingRule).where(SchedulingRule.is_active == True).limit(1)
        result = await db.execute(query)
        rule = result.scalar_one_or_none()
    
    if not rule:
        raise NotFoundException(message="未找到有效的排班规则")
    
    return ApiResponse(code=0, message="success", data=SchedulingRuleResponse.model_validate(rule))


@router.get("/{rule_id}", response_model=ApiResponse[SchedulingRuleResponse])
async def get_scheduling_rule(
    rule_id: int,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取排班规则详情"""
    query = select(SchedulingRule).where(SchedulingRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise NotFoundException(message="排班规则不存在")
    
    return ApiResponse(code=0, message="success", data=SchedulingRuleResponse.model_validate(rule))


@router.post("", response_model=ApiResponse[SchedulingRuleResponse], status_code=status.HTTP_201_CREATED)
async def create_scheduling_rule(
    rule_data: SchedulingRuleCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """创建排班规则"""
    existing_query = select(SchedulingRule).where(SchedulingRule.name == rule_data.name)
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        raise ConflictException(message="规则名称已存在")
    
    if rule_data.is_default:
        await db.execute(
            select(SchedulingRule).where(SchedulingRule.is_default == True)
        )
        existing_defaults = (await db.execute(
            select(SchedulingRule).where(SchedulingRule.is_default == True)
        )).scalars().all()
        for r in existing_defaults:
            r.is_default = False
    
    rule = SchedulingRule(**rule_data.model_dump())
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    return ApiResponse(code=0, message="创建成功", data=SchedulingRuleResponse.model_validate(rule))


@router.put("/{rule_id}", response_model=ApiResponse[SchedulingRuleResponse])
async def update_scheduling_rule(
    rule_id: int,
    rule_data: SchedulingRuleUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """更新排班规则"""
    query = select(SchedulingRule).where(SchedulingRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise NotFoundException(message="排班规则不存在")
    
    if rule_data.is_default:
        existing_defaults = (await db.execute(
            select(SchedulingRule).where(
                (SchedulingRule.is_default == True) &
                (SchedulingRule.id != rule_id)
            )
        )).scalars().all()
        for r in existing_defaults:
            r.is_default = False
    
    update_data = rule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    await db.commit()
    await db.refresh(rule)
    
    return ApiResponse(code=0, message="更新成功", data=SchedulingRuleResponse.model_validate(rule))


@router.delete("/{rule_id}", response_model=ApiResponse[dict])
async def delete_scheduling_rule(
    rule_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """删除排班规则（软删除）"""
    query = select(SchedulingRule).where(SchedulingRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise NotFoundException(message="排班规则不存在")
    
    if rule.is_default:
        raise ConflictException(message="不能删除默认规则，请先设置其他规则为默认")
    
    rule.is_active = False
    await db.commit()
    
    return ApiResponse(code=0, message="删除成功", data={})


@router.post("/{rule_id}/set-default", response_model=ApiResponse[dict])
async def set_default_rule(
    rule_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """设置为默认规则"""
    query = select(SchedulingRule).where(SchedulingRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise NotFoundException(message="排班规则不存在")
    
    if not rule.is_active:
        raise ConflictException(message="不能将已停用的规则设为默认")
    
    existing_defaults = (await db.execute(
        select(SchedulingRule).where(
            (SchedulingRule.is_default == True) &
            (SchedulingRule.id != rule_id)
        )
    )).scalars().all()
    for r in existing_defaults:
        r.is_default = False
    
    rule.is_default = True
    await db.commit()
    
    return ApiResponse(code=0, message="设置成功", data={})
