from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.cat_rooms import router as cat_rooms_router
from app.api.v1.services import router as services_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.members import router as members_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(cat_rooms_router, prefix="/cat-rooms", tags=["猫屋管理"])
api_router.include_router(services_router, prefix="/services", tags=["服务套餐"])
api_router.include_router(bookings_router, prefix="/bookings", tags=["预订管理"])
api_router.include_router(members_router, prefix="/members", tags=["会员管理"])

__all__ = ["api_router"]
