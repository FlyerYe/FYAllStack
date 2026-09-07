import unittest
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient
from pwdlib import PasswordHash

from app.core.config import settings
from app.db.database import get_connection
from app.db.redis import redis_client
from app.main import app
from app.services.cache_service import (
    CACHE_PREFIX,
    categories_cache_key,
    recipe_detail_cache_key,
    recipes_list_cache_key,
)


def clear_recipe_order_cache() -> None:
    keys = list(redis_client.scan_iter(match=f"{CACHE_PREFIX}:*"))
    if keys:
        redis_client.delete(*keys)


class CacheAsideTests(unittest.TestCase):
    def test_recipe_and_category_cache_aside_and_invalidation(self):
        suffix = uuid.uuid4().hex
        admin_username = f"__phase9_admin_{suffix}"
        user_username = f"__phase9_user_{suffix}"
        password = f"phase9-{suffix}"
        category_name = f"缓存分类-{suffix}"
        updated_category_name = f"更新缓存分类-{suffix}"
        recipe_name = f"缓存菜谱-{suffix}"
        category_id = None
        recipe_id = None
        setup_conn = get_connection()
        try:
            password_hash = PasswordHash.recommended()
            with setup_conn.transaction():
                with setup_conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO users (username, password_hash, role)
                        VALUES (%s, %s, 'admin'), (%s, %s, 'user')
                        """,
                        (
                            admin_username,
                            password_hash.hash(password),
                            user_username,
                            password_hash.hash(password),
                        ),
                    )
                    cursor.execute(
                        "INSERT INTO recipe_categories (name) VALUES (%s) RETURNING id",
                        (category_name,),
                    )
                    category_id = cursor.fetchone()[0]
                    cursor.execute(
                        """
                        INSERT INTO recipes (name, price, category_id, status)
                        VALUES (%s, 18.50, %s, 'active')
                        RETURNING id
                        """,
                        (recipe_name, category_id),
                    )
                    recipe_id = cursor.fetchone()[0]

            clear_recipe_order_cache()
            client = TestClient(app)
            admin_login = client.post(
                "/api/auth/login",
                json={"username": admin_username, "password": password},
            )
            user_login = client.post(
                "/api/auth/login",
                json={"username": user_username, "password": password},
            )
            self.assertEqual(admin_login.status_code, 200)
            self.assertEqual(user_login.status_code, 200)
            admin_headers = {
                "Authorization": f"Bearer {admin_login.json()['access_token']}"
            }
            user_headers = {
                "Authorization": f"Bearer {user_login.json()['access_token']}"
            }

            category_response = client.get("/api/categories", headers=user_headers)
            self.assertEqual(category_response.status_code, 200)
            category_key = categories_cache_key()
            self.assertGreater(redis_client.ttl(category_key), 0)
            with patch(
                "app.services.category_service.get_connection",
                side_effect=AssertionError("category cache miss"),
            ):
                cached_categories = client.get("/api/categories", headers=user_headers)
            self.assertEqual(cached_categories.status_code, 200)
            self.assertEqual(cached_categories.json(), category_response.json())

            user_list = client.get(
                f"/api/recipes?category_id={category_id}", headers=user_headers
            )
            self.assertEqual(user_list.status_code, 200)
            user_list_key = recipes_list_cache_key(
                "user", 1, 10, category_id, None
            )
            self.assertGreater(redis_client.ttl(user_list_key), 0)
            with patch(
                "app.services.recipe_service.get_connection",
                side_effect=AssertionError("recipe cache miss"),
            ):
                cached_user_list = client.get(
                    f"/api/recipes?category_id={category_id}", headers=user_headers
                )
            self.assertEqual(cached_user_list.status_code, 200)
            self.assertEqual(cached_user_list.json(), user_list.json())

            admin_list = client.get(
                f"/api/recipes?category_id={category_id}", headers=admin_headers
            )
            self.assertEqual(admin_list.status_code, 200)
            admin_list_key = recipes_list_cache_key(
                "admin", 1, 10, category_id, None
            )
            self.assertTrue(redis_client.exists(admin_list_key))
            self.assertNotEqual(user_list_key, admin_list_key)

            recipe_detail = client.get(
                f"/api/recipes/{recipe_id}", headers=user_headers
            )
            self.assertEqual(recipe_detail.status_code, 200)
            detail_key = recipe_detail_cache_key("user", recipe_id)
            self.assertGreater(redis_client.ttl(detail_key), 0)

            updated_recipe = client.put(
                f"/api/recipes/{recipe_id}",
                json={"price": 22.75},
                headers=admin_headers,
            )
            self.assertEqual(updated_recipe.status_code, 200)
            self.assertFalse(redis_client.exists(user_list_key))
            self.assertFalse(redis_client.exists(admin_list_key))
            self.assertFalse(redis_client.exists(detail_key))
            refreshed_user_list = client.get(
                f"/api/recipes?category_id={category_id}", headers=user_headers
            )
            self.assertEqual(refreshed_user_list.status_code, 200)
            self.assertEqual(refreshed_user_list.json()["items"][0]["price"], 22.75)

            categories_after_recipe_update = client.get(
                "/api/categories", headers=user_headers
            )
            self.assertEqual(categories_after_recipe_update.status_code, 200)
            self.assertTrue(redis_client.exists(category_key))
            category_update = client.put(
                f"/api/categories/{category_id}",
                json={"name": updated_category_name},
                headers=admin_headers,
            )
            self.assertEqual(category_update.status_code, 200)
            self.assertFalse(redis_client.exists(category_key))
            refreshed_categories = client.get("/api/categories", headers=user_headers)
            self.assertEqual(refreshed_categories.status_code, 200)
            self.assertIn(
                updated_category_name,
                [item["name"] for item in refreshed_categories.json()],
            )
            print("cache_miss_and_hit=passed")
            print("cache_key_isolation=passed")
            print("cache_ttl=passed")
            print("cache_write_invalidation=passed")
        finally:
            setup_conn.close()
            cleanup_conn = get_connection()
            try:
                with cleanup_conn.transaction():
                    with cleanup_conn.cursor() as cursor:
                        if recipe_id is not None:
                            cursor.execute("DELETE FROM recipes WHERE id = %s", (recipe_id,))
                        if category_id is not None:
                            cursor.execute(
                                "DELETE FROM recipe_categories WHERE id = %s",
                                (category_id,),
                            )
                        cursor.execute(
                            "DELETE FROM users WHERE username IN (%s, %s)",
                            (admin_username, user_username),
                        )
            finally:
                cleanup_conn.close()
                clear_recipe_order_cache()


if __name__ == "__main__":
    unittest.main()
