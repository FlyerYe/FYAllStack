import psycopg
from fastapi import HTTPException

from app.db.database import get_connection
from app.schemas.categories import CategoryCreate, CategoryUpdate
from app.services.cache_service import (
    categories_cache_key,
    get_cached_json,
    invalidate_category_cache,
    set_cached_json,
)


def _serialize_category(row: tuple) -> dict:
    return {
        "id": row[0],
        "name": row[1],
        "created_at": row[2].isoformat() if row[2] else None,
    }


def get_categories_service() -> list[dict]:
    cache_key = categories_cache_key()
    cached_categories = get_cached_json(cache_key)
    if cached_categories is not None:
        return cached_categories

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name, created_at
                    FROM recipe_categories
                    ORDER BY id ASC
                    """
                )
                rows = cursor.fetchall()
        categories = [_serialize_category(row) for row in rows]
        set_cached_json(cache_key, categories)
        return categories
    finally:
        conn.close()


def create_category_service(category: CategoryCreate) -> dict:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO recipe_categories (name)
                    VALUES (%s)
                    RETURNING id, name, created_at
                    """,
                    (category.name,),
                )
                row = cursor.fetchone()
        result = _serialize_category(row)
        invalidate_category_cache()
        return result
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="分类名称已存在")
    finally:
        conn.close()


def update_category_service(category_id: int, category: CategoryUpdate) -> dict:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE recipe_categories
                    SET name = %s
                    WHERE id = %s
                    RETURNING id, name, created_at
                    """,
                    (category.name, category_id),
                )
                row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="分类不存在")
        result = _serialize_category(row)
        invalidate_category_cache()
        return result
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="分类名称已存在")
    finally:
        conn.close()


def delete_category_service(category_id: int) -> dict:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM recipe_categories
                    WHERE id = %s
                    RETURNING id
                    """,
                    (category_id,),
                )
                row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="分类不存在")
        result = {"message": "删除成功", "id": row[0]}
        invalidate_category_cache()
        return result
    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(status_code=409, detail="分类正在被使用，无法删除")
    finally:
        conn.close()
