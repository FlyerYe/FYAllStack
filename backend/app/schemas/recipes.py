from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


RecipeStatus = Literal["active", "inactive"]


def _normalize_name(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("菜谱名称不能为空")
    return normalized


class RecipeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    price: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=10,
        decimal_places=2,
    )
    category_id: int = Field(gt=0)
    image_url: str | None = Field(default=None, max_length=500)
    status: RecipeStatus = "active"

    @field_validator("name")
    @classmethod
    def normalize_recipe_name(cls, value: str) -> str:
        return _normalize_name(value)


class RecipeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
    )
    category_id: int | None = Field(default=None, gt=0)
    image_url: str | None = Field(default=None, max_length=500)
    status: RecipeStatus | None = None

    @field_validator("name")
    @classmethod
    def normalize_recipe_name(cls, value: str | None) -> str | None:
        return _normalize_name(value) if value is not None else None


class RecipeResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    image_url: str | None
    category_id: int
    category_name: str
    status: RecipeStatus
    created_at: str | None
    updated_at: str | None


class RecipeListResponse(BaseModel):
    items: list[RecipeResponse]
    page: int
    page_size: int
    total: int
