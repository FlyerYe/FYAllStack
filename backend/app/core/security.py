from typing import Literal, TypedDict

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings


UserRole = Literal["admin", "user"]


class CurrentUser(TypedDict):
    user_id: int
    role: UserRole


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
)


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token 已过期")
    except jwt.InvalidTokenError:
        raise _unauthorized("无效 Token")

    user_id = payload.get("sub")
    role = payload.get("role")

    if user_id is None or role not in ("admin", "user"):
        raise _unauthorized("无效 Token")

    try:
        parsed_user_id = int(user_id)
    except (TypeError, ValueError):
        raise _unauthorized("无效 Token")

    return {
        "user_id": parsed_user_id,
        "role": role,
    }


def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限",
        )

    return current_user
