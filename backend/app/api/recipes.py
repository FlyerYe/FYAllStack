from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import CurrentUser, get_current_user, require_admin
from app.schemas.recipes import (
    RecipeCreate,
    RecipeListResponse,
    RecipeResponse,
    RecipeStatus,
    RecipeUpdate,
)
from app.services.recipe_service import (
    create_recipe_service,
    delete_recipe_service,
    get_recipe_service,
    get_recipes_service,
    update_recipe_service,
)


router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.get("", response_model=RecipeListResponse)
def get_recipes(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    category_id: Annotated[int | None, Query(gt=0)] = None,
    status: RecipeStatus | None = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    return get_recipes_service(
        current_user,
        page,
        page_size,
        category_id,
        status,
    )


@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(
    recipe_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    return get_recipe_service(recipe_id, current_user)


@router.post("", response_model=RecipeResponse)
def create_recipe(
    recipe: RecipeCreate,
    _: CurrentUser = Depends(require_admin),
):
    return create_recipe_service(recipe)


@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: int,
    recipe: RecipeUpdate,
    _: CurrentUser = Depends(require_admin),
):
    return update_recipe_service(recipe_id, recipe)


@router.delete("/{recipe_id}")
def delete_recipe(
    recipe_id: int,
    _: CurrentUser = Depends(require_admin),
):
    return delete_recipe_service(recipe_id)
