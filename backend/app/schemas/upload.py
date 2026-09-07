from pydantic import BaseModel, Field


class ImageUploadResponse(BaseModel):
    url: str = Field(min_length=1, max_length=2000)
