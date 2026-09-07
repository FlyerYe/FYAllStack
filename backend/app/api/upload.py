from fastapi import APIRouter, Depends, File, UploadFile

from app.core.security import CurrentUser, require_admin
from app.schemas.upload import ImageUploadResponse
from app.services.oss import upload_image_service


router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/image", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    _: CurrentUser = Depends(require_admin),
):
    return await upload_image_service(file)
