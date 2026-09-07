from fastapi import APIRouter, HTTPException
from pwdlib import PasswordHash

from app.db.database import get_connection
from app.schemas.user import UserRegister, LoginRequest

from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.exceptions import AppException
from app.core.security import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])
password_hash = PasswordHash.recommended()

@router.post("/register")
def register(user: UserRegister):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                # Check if the username already exists
                cursor.execute(
                    "SELECT id FROM users WHERE username = %s", (user.username,)
                )
                existing_user = cursor.fetchone()
                if existing_user:
                    raise HTTPException(status_code=400, detail="用户名已存在")

                # Hash the password
                hashed_password = password_hash.hash(user.password)

                # Insert the new user into the database
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id, username",
                    (user.username, hashed_password),
                )
                result = cursor.fetchone()
                
                return {
                    "id": result[0],
                    "username": result[1],
                }
                
    finally:
        conn.close()


def create_access_token(user_id: int, role: str):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes,
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }
    encoded_jwt = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

@router.post("/login")
def login(user: LoginRequest):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, username, password_hash, role
                    FROM users
                    WHERE username = %s
                    """,
                    (user.username,),
                )
                result = cursor.fetchone()
                if not result:
                    # raise HTTPException(status_code=401, detail="用户名不存在")
                    raise AppException(message="用户名不存在", status_code=401)
                user_id, username, password_hash_db, role = result
                if not password_hash.verify(user.password, password_hash_db):
                    raise AppException(message="密码错误", status_code=401)
                access_token = create_access_token(user_id, role)
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "role": role,
                }
    finally:
        conn.close()
