from __future__ import annotations

from urllib.parse import quote, urlparse
from uuid import uuid4

import oss2
from fastapi import HTTPException, UploadFile

from app.core.config import settings


MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _has_valid_image_signature(content_type: str, content: bytes) -> bool:
    signatures = {
        "image/jpeg": (content.startswith(b"\xff\xd8\xff"),),
        "image/png": (content.startswith(b"\x89PNG\r\n\x1a\n"),),
        "image/webp": (
            len(content) >= 12
            and content[:4] == b"RIFF"
            and content[8:12] == b"WEBP",
        ),
    }
    return all(signatures[content_type])


def _require_oss_config() -> tuple[str, str, str, str, str, str]:
    values = (
        settings.oss_access_key_id,
        settings.oss_access_key_secret,
        settings.oss_region,
        settings.oss_bucket,
        settings.oss_endpoint,
        settings.oss_domain or settings.oss_endpoint,
    )
    if any(not value for value in values):
        raise HTTPException(status_code=503, detail="OSS 配置不完整")
    return values  # type: ignore[return-value]


def _normalize_endpoint(value: str) -> str:
    if value.startswith(("http://", "https://")):
        return value.rstrip("/")
    return f"https://{value.rstrip('/')}"


def _resolve_upload_endpoint(endpoint: str, domain: str, region: str) -> str:
    normalized_endpoint = _normalize_endpoint(endpoint)
    normalized_domain = _normalize_endpoint(domain)
    if urlparse(normalized_endpoint).netloc == urlparse(normalized_domain).netloc:
        return f"https://oss-{region}.aliyuncs.com"
    return normalized_endpoint


def _build_bucket() -> oss2.Bucket:
    access_key_id, access_key_secret, region, bucket_name, endpoint, domain = (
        _require_oss_config()
    )
    auth = oss2.Auth(access_key_id, access_key_secret)
    upload_endpoint = _resolve_upload_endpoint(endpoint, domain, region)
    return oss2.Bucket(auth, upload_endpoint, bucket_name)


async def upload_image_service(file: UploadFile) -> dict[str, str]:
    extension = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if extension is None:
        raise HTTPException(
            status_code=415,
            detail="仅支持 JPEG、PNG 和 WebP 图片",
        )

    content = await file.read(MAX_IMAGE_SIZE + 1)
    if not content:
        raise HTTPException(status_code=400, detail="图片文件不能为空")
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="图片大小不能超过 5 MB")
    if not _has_valid_image_signature(file.content_type or "", content):
        raise HTTPException(status_code=415, detail="图片内容与文件类型不匹配")

    object_key = f"recipes/{uuid4().hex}.{extension}"
    _, _, _, _, _, domain = _require_oss_config()
    try:
        _build_bucket().put_object(
            object_key,
            content,
            headers={"Content-Type": file.content_type},
        )
    except oss2.exceptions.OssError as exc:
        raise HTTPException(status_code=502, detail="OSS 图片上传失败") from exc

    return {"url": f"{domain.rstrip('/')}/{quote(object_key)}"}
