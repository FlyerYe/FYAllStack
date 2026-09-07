import unittest
import uuid

from fastapi.testclient import TestClient
from pwdlib import PasswordHash

from app.db.database import get_connection
from app.main import app


class RecipeApiTests(unittest.TestCase):
    def test_recipe_crud_visibility_filtering_and_pagination(self):
        suffix = uuid.uuid4().hex
        admin_username = f"__phase3_admin_{suffix}"
        user_username = f"__phase3_user_{suffix}"
        password = f"phase3-{suffix}"
        category_name = f"菜谱分类-{suffix}"
        active_name = f"上架菜谱-{suffix}"
        inactive_name = f"下架菜谱-{suffix}"
        updated_name = f"更新菜谱-{suffix}"

        setup_conn = get_connection()
        try:
            password_hash = PasswordHash.recommended()
            with setup_conn.transaction():
                with setup_conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                        (admin_username, password_hash.hash(password), "admin"),
                    )
                    cursor.execute(
                        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                        (user_username, password_hash.hash(password), "user"),
                    )
                    cursor.execute(
                        "INSERT INTO recipe_categories (name) VALUES (%s) RETURNING id",
                        (category_name,),
                    )
                    category_id = cursor.fetchone()[0]

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

            invalid_price = client.post(
                "/api/recipes",
                json={"name": active_name, "price": -1, "category_id": category_id},
                headers=admin_headers,
            )
            self.assertEqual(invalid_price.status_code, 422)

            missing_category = client.post(
                "/api/recipes",
                json={"name": active_name, "price": 12, "category_id": 999999},
                headers=admin_headers,
            )
            self.assertEqual(missing_category.status_code, 404)

            user_create = client.post(
                "/api/recipes",
                json={"name": active_name, "price": 12, "category_id": category_id},
                headers=user_headers,
            )
            self.assertEqual(user_create.status_code, 403)

            active_create = client.post(
                "/api/recipes",
                json={
                    "name": f"  {active_name}  ",
                    "description": "可见菜谱",
                    "price": "12.50",
                    "category_id": category_id,
                    "image_url": None,
                },
                headers=admin_headers,
            )
            self.assertEqual(active_create.status_code, 200)
            active_recipe = active_create.json()
            active_id = active_recipe["id"]
            self.assertEqual(active_recipe["name"], active_name)
            self.assertEqual(active_recipe["price"], 12.5)
            self.assertEqual(active_recipe["status"], "active")
            self.assertIsNone(active_recipe["image_url"])

            inactive_create = client.post(
                "/api/recipes",
                json={
                    "name": inactive_name,
                    "price": 20,
                    "category_id": category_id,
                    "status": "inactive",
                },
                headers=admin_headers,
            )
            self.assertEqual(inactive_create.status_code, 200)
            inactive_id = inactive_create.json()["id"]

            user_list = client.get(
                f"/api/recipes?category_id={category_id}", headers=user_headers
            )
            self.assertEqual(user_list.status_code, 200)
            self.assertEqual(user_list.json()["total"], 1)
            self.assertEqual(
                [item["name"] for item in user_list.json()["items"]],
                [active_name],
            )

            user_inactive_filter = client.get(
                f"/api/recipes?status=inactive&category_id={category_id}",
                headers=user_headers,
            )
            self.assertEqual(user_inactive_filter.status_code, 200)
            self.assertEqual(user_inactive_filter.json()["total"], 1)

            admin_list = client.get(
                f"/api/recipes?category_id={category_id}", headers=admin_headers
            )
            self.assertEqual(admin_list.status_code, 200)
            self.assertEqual(admin_list.json()["total"], 2)

            category_filter = client.get(
                f"/api/recipes?category_id={category_id}&page=1&page_size=1",
                headers=admin_headers,
            )
            self.assertEqual(category_filter.status_code, 200)
            self.assertEqual(category_filter.json()["total"], 2)
            self.assertEqual(len(category_filter.json()["items"]), 1)
            self.assertEqual(category_filter.json()["page"], 1)
            self.assertEqual(category_filter.json()["page_size"], 1)

            user_active_detail = client.get(
                f"/api/recipes/{active_id}",
                headers=user_headers,
            )
            self.assertEqual(user_active_detail.status_code, 200)

            user_inactive_detail = client.get(
                f"/api/recipes/{inactive_id}",
                headers=user_headers,
            )
            self.assertEqual(user_inactive_detail.status_code, 404)

            admin_inactive_detail = client.get(
                f"/api/recipes/{inactive_id}",
                headers=admin_headers,
            )
            self.assertEqual(admin_inactive_detail.status_code, 200)
            self.assertEqual(admin_inactive_detail.json()["status"], "inactive")

            user_update = client.put(
                f"/api/recipes/{active_id}",
                json={"name": updated_name},
                headers=user_headers,
            )
            self.assertEqual(user_update.status_code, 403)

            admin_update = client.put(
                f"/api/recipes/{active_id}",
                json={"name": updated_name, "status": "inactive"},
                headers=admin_headers,
            )
            self.assertEqual(admin_update.status_code, 200)
            self.assertEqual(admin_update.json()["name"], updated_name)
            self.assertEqual(admin_update.json()["status"], "inactive")

            user_after_offline = client.get(
                f"/api/recipes?category_id={category_id}", headers=user_headers
            )
            self.assertEqual(user_after_offline.status_code, 200)
            self.assertEqual(user_after_offline.json()["total"], 0)

            user_delete = client.delete(
                f"/api/recipes/{inactive_id}",
                headers=user_headers,
            )
            self.assertEqual(user_delete.status_code, 403)

            admin_delete = client.delete(
                f"/api/recipes/{inactive_id}",
                headers=admin_headers,
            )
            self.assertEqual(admin_delete.status_code, 200)

            missing_delete = client.delete(
                f"/api/recipes/{inactive_id}",
                headers=admin_headers,
            )
            self.assertEqual(missing_delete.status_code, 404)
        finally:
            setup_conn.close()
            cleanup_conn = get_connection()
            try:
                with cleanup_conn.transaction():
                    with cleanup_conn.cursor() as cursor:
                        cursor.execute(
                            "DELETE FROM recipes WHERE name IN (%s, %s, %s)",
                            (active_name, inactive_name, updated_name),
                        )
                        cursor.execute(
                            "DELETE FROM recipe_categories WHERE name = %s",
                            (category_name,),
                        )
                        cursor.execute(
                            "DELETE FROM users WHERE username IN (%s, %s)",
                            (admin_username, user_username),
                        )
            finally:
                cleanup_conn.close()


if __name__ == "__main__":
    unittest.main()
