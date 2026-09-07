from fastapi import APIRouter, Depends

from app.core.security import CurrentUser, get_current_user, require_admin
from app.schemas.categories import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from app.services.category_service import (
    create_category_service,
    delete_category_service,
    get_categories_service,
    update_category_service,
)


router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def get_categories(
    _: CurrentUser = Depends(get_current_user),
):
    return get_categories_service()


@router.post("", response_model=CategoryResponse)
def create_category(
    category: CategoryCreate,
    _: CurrentUser = Depends(require_admin),
):
    return create_category_service(category)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category: CategoryUpdate,
    _: CurrentUser = Depends(require_admin),
):
    return update_category_service(category_id, category)


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    _: CurrentUser = Depends(require_admin),
):
    return delete_category_service(category_id)
