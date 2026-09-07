from pydantic import BaseModel, Field, field_validator


class CategoryName(BaseModel):
    name: str = Field(min_length=1, max_length=50)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("分类名称不能为空")
        return normalized


class CategoryCreate(CategoryName):
    pass


class CategoryUpdate(CategoryName):
    pass


class CategoryResponse(BaseModel):
    id: int
    name: str
    created_at: str | None
