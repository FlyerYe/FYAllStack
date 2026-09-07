import psycopg
from fastapi import HTTPException

from app.core.security import CurrentUser
from app.db.database import get_connection
from app.schemas.recipes import RecipeCreate, RecipeStatus, RecipeUpdate
from app.services.cache_service import (
    get_cached_json,
    invalidate_recipe_cache,
    recipe_detail_cache_key,
    recipes_list_cache_key,
    set_cached_json,
)


RECIPE_SELECT = """
    SELECT
        r.id,
        r.name,
        r.description,
        r.price,
        r.image_url,
        r.category_id,
        c.name,
        r.status,
        r.created_at,
        r.updated_at
    FROM recipes r
    JOIN recipe_categories c ON c.id = r.category_id
"""


def _serialize_recipe(row: tuple) -> dict:
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "price": float(row[3]),
        "image_url": row[4],
        "category_id": row[5],
        "category_name": row[6],
        "status": row[7],
        "created_at": row[8].isoformat() if row[8] else None,
        "updated_at": row[9].isoformat() if row[9] else None,
    }


def _category_exists(cursor, category_id: int) -> bool:
    cursor.execute(
        "SELECT 1 FROM recipe_categories WHERE id = %s",
        (category_id,),
    )
    return cursor.fetchone() is not None


def _raise_category_not_found() -> None:
    raise HTTPException(status_code=404, detail="分类不存在")


def get_recipes_service(
    current_user: CurrentUser,
    page: int,
    page_size: int,
    category_id: int | None,
    status: RecipeStatus | None,
) -> dict:
    cache_key = recipes_list_cache_key(
        current_user["role"], page, page_size, category_id, status
    )
    cached_recipes = get_cached_json(cache_key)
    if cached_recipes is not None:
        return cached_recipes

    conditions = ["1 = 1"]
    filter_params: list[object] = []

    if current_user["role"] == "admin":
        if status is not None:
            conditions.append("r.status = %s")
            filter_params.append(status)
    else:
        conditions.append("r.status = 'active'")

    if category_id is not None:
        conditions.append("r.category_id = %s")
        filter_params.append(category_id)

    where_clause = " AND ".join(conditions)
    offset = (page - 1) * page_size

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT COUNT(*) FROM recipes r WHERE {where_clause}",
                    tuple(filter_params),
                )
                total = cursor.fetchone()[0]

                cursor.execute(
                    f"""
                    {RECIPE_SELECT}
                    WHERE {where_clause}
                    ORDER BY r.id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (*filter_params, page_size, offset),
                )
                rows = cursor.fetchall()

        result = {
            "items": [_serialize_recipe(row) for row in rows],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
        set_cached_json(cache_key, result)
        return result
    finally:
        conn.close()


def get_recipe_service(recipe_id: int, current_user: CurrentUser) -> dict:
    cache_key = recipe_detail_cache_key(current_user["role"], recipe_id)
    cached_recipe = get_cached_json(cache_key)
    if cached_recipe is not None:
        return cached_recipe

    conditions = ["r.id = %s"]
    params: list[object] = [recipe_id]
    if current_user["role"] != "admin":
        conditions.append("r.status = 'active'")

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    {RECIPE_SELECT}
                    WHERE {' AND '.join(conditions)}
                    """,
                    tuple(params),
                )
                row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="菜谱不存在")
        result = _serialize_recipe(row)
        set_cached_json(cache_key, result)
        return result
    finally:
        conn.close()


def create_recipe_service(recipe: RecipeCreate) -> dict:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                if not _category_exists(cursor, recipe.category_id):
                    _raise_category_not_found()

                cursor.execute(
                    """
                    INSERT INTO recipes
                        (name, description, price, image_url, category_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        recipe.name,
                        recipe.description,
                        recipe.price,
                        recipe.image_url,
                        recipe.category_id,
                        recipe.status,
                    ),
                )
                recipe_id = cursor.fetchone()[0]
        invalidate_recipe_cache()
        return get_recipe_service(recipe_id, {"user_id": 0, "role": "admin"})
    except psycopg.errors.ForeignKeyViolation:
        _raise_category_not_found()
    finally:
        conn.close()


def update_recipe_service(recipe_id: int, recipe: RecipeUpdate) -> dict:
    values = recipe.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=400, detail="至少提供一个需要修改的字段")

    field_map = {
        "name": "name",
        "description": "description",
        "price": "price",
        "image_url": "image_url",
        "category_id": "category_id",
        "status": "status",
    }
    assignments = [f"{field_map[field]} = %s" for field in values]
    params = [values[field] for field in values]
    assignments.append("updated_at = CURRENT_TIMESTAMP")
    params.append(recipe_id)

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                if "category_id" in values and not _category_exists(
                    cursor,
                    values["category_id"],
                ):
                    _raise_category_not_found()

                cursor.execute(
                    f"""
                    UPDATE recipes
                    SET {', '.join(assignments)}
                    WHERE id = %s
                    RETURNING id
                    """,
                    tuple(params),
                )
                row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="菜谱不存在")
        invalidate_recipe_cache()
        return get_recipe_service(row[0], {"user_id": 0, "role": "admin"})
    except psycopg.errors.ForeignKeyViolation:
        _raise_category_not_found()
    finally:
        conn.close()


def delete_recipe_service(recipe_id: int) -> dict:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM recipes WHERE id = %s RETURNING id",
                    (recipe_id,),
                )
                row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="菜谱不存在")
        result = {"message": "删除成功", "id": row[0]}
        invalidate_recipe_cache()
        return result
    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(status_code=409, detail="菜谱已有订单记录，无法物理删除")
    finally:
        conn.close()
