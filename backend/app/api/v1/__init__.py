from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.cat_rooms import router as cat_rooms_router
from app.api.v1.services import router as services_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.members import router as members_router
from app.api.v1.employees import router as employees_router
from app.api.v1.shifts import router as shifts_router
from app.api.v1.scheduling_rules import router as scheduling_rules_router
from app.api.v1.schedules import router as schedules_router
from app.api.v1.leave_requests import router as leave_requests_router
from app.api.v1.shift_swaps import router as shift_swaps_router
from app.api.v1.shift_preferences import router as shift_preferences_router
from app.api.v1.attendances import router as attendances_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(cat_rooms_router, prefix="/cat-rooms", tags=["猫屋管理"])
api_router.include_router(services_router, prefix="/services", tags=["服务套餐"])
api_router.include_router(bookings_router, prefix="/bookings", tags=["预订管理"])
api_router.include_router(members_router, prefix="/members", tags=["会员管理"])
api_router.include_router(employees_router, prefix="/employees", tags=["员工管理"])
api_router.include_router(shifts_router, prefix="/shifts", tags=["班次管理"])
api_router.include_router(scheduling_rules_router, prefix="/scheduling-rules", tags=["排班规则"])
api_router.include_router(schedules_router, prefix="/schedules", tags=["排班管理"])
api_router.include_router(leave_requests_router, prefix="/leave-requests", tags=["请假申请"])
api_router.include_router(shift_swaps_router, prefix="/shift-swaps", tags=["调班申请"])
api_router.include_router(shift_preferences_router, prefix="/shift-preferences", tags=["班次偏好"])
api_router.include_router(attendances_router, prefix="/attendances", tags=["考勤管理"])

__all__ = ["api_router"]
