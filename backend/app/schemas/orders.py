from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


OrderStatus = Literal["pending", "completed", "cancelled"]


class OrderItemCreate(BaseModel):
    recipe_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=99)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1, max_length=50)


class AdminOrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderItemResponse(BaseModel):
    id: int
    recipe_id: int
    recipe_name: str
    image_url: str | None
    quantity: int
    price: Decimal
    subtotal: Decimal


class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    total_amount: Decimal
    created_at: str | None
    updated_at: str | None
    items: list[OrderItemResponse]
