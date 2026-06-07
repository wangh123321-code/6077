from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict


T = TypeVar("T")


class PaginationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")


class PaginationResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ApiResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
