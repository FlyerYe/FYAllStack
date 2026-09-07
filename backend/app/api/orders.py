from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import CurrentUser, get_current_user, require_admin
from app.schemas.orders import (
    AdminOrderStatusUpdate,
    OrderCreate,
    OrderResponse,
    OrderStatus,
)
from app.services.order_service import (
    cancel_order_service,
    create_order_service,
    get_admin_order_service,
    get_admin_orders_service,
    get_order_service,
    get_orders_service,
    update_admin_order_status_service,
)


router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderResponse)
def create_order(
    order: OrderCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    return create_order_service(order, current_user)


@router.get("", response_model=list[OrderResponse])
def get_orders(
    current_user: CurrentUser = Depends(get_current_user),
):
    return get_orders_service(current_user)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    return get_order_service(order_id, current_user["user_id"])


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    return cancel_order_service(order_id, current_user)


admin_router = APIRouter(prefix="/api/admin/orders", tags=["admin-orders"])


@admin_router.get("", response_model=list[OrderResponse])
def get_admin_orders(
    status: Annotated[OrderStatus | None, Query()] = None,
    _: CurrentUser = Depends(require_admin),
):
    return get_admin_orders_service(status)


@admin_router.get("/{order_id}", response_model=OrderResponse)
def get_admin_order(
    order_id: int,
    _: CurrentUser = Depends(require_admin),
):
    return get_admin_order_service(order_id)


@admin_router.put("/{order_id}/status", response_model=OrderResponse)
def update_admin_order_status(
    order_id: int,
    status_update: AdminOrderStatusUpdate,
    _: CurrentUser = Depends(require_admin),
):
    return update_admin_order_status_service(order_id, status_update)
