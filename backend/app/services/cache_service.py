from __future__ import annotations

import json
from typing import Any

import redis

from app.core.config import settings
from app.core.logger import logger
from app.db.redis import redis_client


CACHE_PREFIX = "recipe-order:v1"


def _get_json(key: str) -> Any | None:
    try:
        value = redis_client.get(key)
    except redis.RedisError as exc:
        logger.warning("Redis read failed for %s: %s", key, exc)
        return None

    if value is None:
        return None

    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        logger.warning("Invalid Redis cache value for %s: %s", key, exc)
        _delete_keys(key)
        return None


def _set_json(key: str, value: Any) -> None:
    try:
        redis_client.set(
            key,
            json.dumps(value, ensure_ascii=False, separators=(",", ":")),
            ex=settings.cache_ttl_seconds,
        )
    except (TypeError, redis.RedisError) as exc:
        logger.warning("Redis write failed for %s: %s", key, exc)


def _delete_keys(*keys: str) -> None:
    if not keys:
        return
    try:
        redis_client.delete(*keys)
    except redis.RedisError as exc:
        logger.warning("Redis delete failed for %s: %s", keys, exc)


def _delete_pattern(pattern: str) -> None:
    try:
        keys = list(redis_client.scan_iter(match=pattern, count=100))
        if keys:
            redis_client.delete(*keys)
    except redis.RedisError as exc:
        logger.warning("Redis pattern delete failed for %s: %s", pattern, exc)


def categories_cache_key() -> str:
    return f"{CACHE_PREFIX}:categories:all"


def recipes_list_cache_key(
    role: str,
    page: int,
    page_size: int,
    category_id: int | None,
    status: str | None,
) -> str:
    category_part = category_id if category_id is not None else "all"
    status_part = status or "all"
    return (
        f"{CACHE_PREFIX}:recipes:list:{role}:"
        f"page={page}:size={page_size}:category={category_part}:status={status_part}"
    )


def recipe_detail_cache_key(role: str, recipe_id: int) -> str:
    return f"{CACHE_PREFIX}:recipes:detail:{role}:{recipe_id}"


def get_cached_json(key: str) -> Any | None:
    return _get_json(key)


def set_cached_json(key: str, value: Any) -> None:
    _set_json(key, value)


def invalidate_category_cache() -> None:
    _delete_keys(categories_cache_key())
    invalidate_recipe_cache()


def invalidate_recipe_cache() -> None:
    _delete_pattern(f"{CACHE_PREFIX}:recipes:list:*")
    _delete_pattern(f"{CACHE_PREFIX}:recipes:detail:*")
