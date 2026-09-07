import unittest
import uuid

from fastapi.testclient import TestClient
from pwdlib import PasswordHash

from app.db.database import get_connection
from app.main import app


class CategoryApiTests(unittest.TestCase):
    def test_category_read_and_admin_crud_permissions(self):
        suffix = uuid.uuid4().hex
        admin_username = f"__phase2_admin_{suffix}"
        user_username = f"__phase2_user_{suffix}"
        password = f"phase2-{suffix}"
        category_name = f"分类-{suffix}"
        updated_category_name = f"更新分类-{suffix}"

        setup_conn = get_connection()
        try:
            password_hash = PasswordHash.recommended()
            with setup_conn.transaction():
                with setup_conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO users (username, password_hash, role)
                        VALUES (%s, %s, %s)
                        """,
                        (admin_username, password_hash.hash(password), "admin"),
                    )
                    cursor.execute(
                        """
                        INSERT INTO users (username, password_hash, role)
                        VALUES (%s, %s, %s)
                        """,
                        (user_username, password_hash.hash(password), "user"),
                    )

            client = TestClient(app)
            anonymous_response = client.get("/api/categories")
            self.assertEqual(anonymous_response.status_code, 401)

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
            self.assertEqual(admin_login.json()["role"], "admin")
            self.assertEqual(user_login.json()["role"], "user")

            admin_headers = {
                "Authorization": f"Bearer {admin_login.json()['access_token']}"
            }
            user_headers = {
                "Authorization": f"Bearer {user_login.json()['access_token']}"
            }

            user_list = client.get("/api/categories", headers=user_headers)
            self.assertEqual(user_list.status_code, 200)
            self.assertIsInstance(user_list.json(), list)

            user_create = client.post(
                "/api/categories",
                json={"name": category_name},
                headers=user_headers,
            )
            self.assertEqual(user_create.status_code, 403)

            admin_create = client.post(
                "/api/categories",
                json={"name": f"  {category_name}  "},
                headers=admin_headers,
            )
            self.assertEqual(admin_create.status_code, 200)
            category = admin_create.json()
            category_id = category["id"]
            self.assertEqual(category["name"], category_name)

            duplicate_create = client.post(
                "/api/categories",
                json={"name": category_name},
                headers=admin_headers,
            )
            self.assertEqual(duplicate_create.status_code, 409)

            user_update = client.put(
                f"/api/categories/{category_id}",
                json={"name": updated_category_name},
                headers=user_headers,
            )
            self.assertEqual(user_update.status_code, 403)

            admin_update = client.put(
                f"/api/categories/{category_id}",
                json={"name": updated_category_name},
                headers=admin_headers,
            )
            self.assertEqual(admin_update.status_code, 200)
            self.assertEqual(admin_update.json()["name"], updated_category_name)

            user_list_after_update = client.get(
                "/api/categories",
                headers=user_headers,
            )
            self.assertEqual(user_list_after_update.status_code, 200)
            self.assertIn(
                updated_category_name,
                [item["name"] for item in user_list_after_update.json()],
            )

            user_delete = client.delete(
                f"/api/categories/{category_id}",
                headers=user_headers,
            )
            self.assertEqual(user_delete.status_code, 403)

            admin_delete = client.delete(
                f"/api/categories/{category_id}",
                headers=admin_headers,
            )
            self.assertEqual(admin_delete.status_code, 200)
            self.assertEqual(admin_delete.json()["id"], category_id)

            missing_delete = client.delete(
                f"/api/categories/{category_id}",
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
                            "DELETE FROM recipe_categories WHERE name IN (%s, %s)",
                            (category_name, updated_category_name),
                        )
                        cursor.execute(
                            "DELETE FROM users WHERE username IN (%s, %s)",
                            (admin_username, user_username),
                        )
            finally:
                cleanup_conn.close()


if __name__ == "__main__":
    unittest.main()
