from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
    )

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None