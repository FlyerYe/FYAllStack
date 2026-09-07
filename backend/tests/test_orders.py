import unittest
import uuid

from fastapi.testclient import TestClient
from pwdlib import PasswordHash

from app.db.database import get_connection
from app.main import app


class OrderApiTests(unittest.TestCase):
    def test_order_transaction_snapshot_isolation_and_cancel_rules(self):
        suffix = uuid.uuid4().hex
        admin_username = f"o7a{suffix}"
        user_username = f"o7u{suffix}"
        other_username = f"o7o{suffix}"
        password = f"order-{suffix}"
        category_name = f"订单分类-{suffix}"
        active_name = f"订单菜谱-{suffix}"
        inactive_name = f"下架菜谱-{suffix}"
        category_id = None
        active_id = None
        inactive_id = None
        order_id = None
        setup_conn = get_connection()
        try:
            password_hash = PasswordHash.recommended()
            with setup_conn.transaction():
                with setup_conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO users (username, password_hash, role)
                        VALUES (%s, %s, %s), (%s, %s, %s), (%s, %s, %s)
                        """,
                        (
                            admin_username,
                            password_hash.hash(password),
                            "admin",
                            user_username,
                            password_hash.hash(password),
                            "user",
                            other_username,
                            password_hash.hash(password),
                            "user",
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
                        VALUES (%s, 12.50, %s, 'active')
                        RETURNING id
                        """,
                        (active_name, category_id),
                    )
                    active_id = cursor.fetchone()[0]
                    cursor.execute(
                        """
                        INSERT INTO recipes (name, price, category_id, status)
                        VALUES (%s, 20.00, %s, 'inactive')
                        RETURNING id
                        """,
                        (inactive_name, category_id),
                    )
                    inactive_id = cursor.fetchone()[0]

            client = TestClient(app)
            admin_login = client.post(
                "/api/auth/login",
                json={"username": admin_username, "password": password},
            )
            user_login = client.post(
                "/api/auth/login",
                json={"username": user_username, "password": password},
            )
            other_login = client.post(
                "/api/auth/login",
                json={"username": other_username, "password": password},
            )
            self.assertEqual(admin_login.status_code, 200)
            self.assertEqual(user_login.status_code, 200)
            self.assertEqual(other_login.status_code, 200)
            admin_headers = {
                "Authorization": f"Bearer {admin_login.json()['access_token']}"
            }
            user_headers = {
                "Authorization": f"Bearer {user_login.json()['access_token']}"
            }
            other_headers = {
                "Authorization": f"Bearer {other_login.json()['access_token']}"
            }

            invalid_payload = client.post(
                "/api/orders",
                json={
                    "items": [
                        {"recipe_id": active_id, "quantity": 1},
                        {"recipe_id": inactive_id, "quantity": 1},
                    ]
                },
                headers=user_headers,
            )
            self.assertEqual(invalid_payload.status_code, 400)
            setup_check = get_connection()
            try:
                with setup_check.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = (SELECT id FROM users WHERE username = %s)", (user_username,))
                    self.assertEqual(cursor.fetchone()[0], 0)
            finally:
                setup_check.close()

            duplicate_items = client.post(
                "/api/orders",
                json={"items": [{"recipe_id": active_id, "quantity": 1}, {"recipe_id": active_id, "quantity": 2}]},
                headers=user_headers,
            )
            self.assertEqual(duplicate_items.status_code, 400)

            invalid_quantity = client.post(
                "/api/orders",
                json={"items": [{"recipe_id": active_id, "quantity": 0}]},
                headers=user_headers,
            )
            self.assertEqual(invalid_quantity.status_code, 422)

            created = client.post(
                "/api/orders",
                json={"items": [{"recipe_id": active_id, "quantity": 2}]},
                headers=user_headers,
            )
            self.assertEqual(created.status_code, 200, created.text)
            order = created.json()
            order_id = order["id"]
            self.assertGreater(order["user_id"], 0)
            self.assertEqual(order["total_amount"], "25.00")
            self.assertEqual(order["items"][0]["price"], "12.50")

            changed_price = client.put(
                f"/api/recipes/{active_id}",
                json={"price": 30},
                headers=admin_headers,
            )
            self.assertEqual(changed_price.status_code, 200, changed_price.text)
            detail_after_price_change = client.get(
                f"/api/orders/{order_id}", headers=user_headers
            )
            self.assertEqual(detail_after_price_change.status_code, 200)
            self.assertEqual(detail_after_price_change.json()["total_amount"], "25.00")
            self.assertEqual(detail_after_price_change.json()["items"][0]["price"], "12.50")

            user_orders = client.get("/api/orders", headers=user_headers)
            self.assertEqual(user_orders.status_code, 200)
            self.assertEqual([item["id"] for item in user_orders.json()], [order_id])
            other_detail = client.get(f"/api/orders/{order_id}", headers=other_headers)
            self.assertEqual(other_detail.status_code, 404)
            other_orders = client.get("/api/orders", headers=other_headers)
            self.assertEqual(other_orders.status_code, 200)
            self.assertEqual(other_orders.json(), [])

            unauthenticated_admin_orders = client.get("/api/admin/orders")
            self.assertEqual(unauthenticated_admin_orders.status_code, 401)
            user_admin_orders = client.get(
                "/api/admin/orders", headers=user_headers
            )
            self.assertEqual(user_admin_orders.status_code, 403)
            admin_orders = client.get("/api/admin/orders", headers=admin_headers)
            self.assertEqual(admin_orders.status_code, 200)
            self.assertIn(order_id, [item["id"] for item in admin_orders.json()])
            admin_order_detail = client.get(
                f"/api/admin/orders/{order_id}", headers=admin_headers
            )
            self.assertEqual(admin_order_detail.status_code, 200)
            user_admin_detail = client.get(
                f"/api/admin/orders/{order_id}", headers=user_headers
            )
            self.assertEqual(user_admin_detail.status_code, 403)

            cancelled = client.post(
                f"/api/orders/{order_id}/cancel", headers=user_headers
            )
            self.assertEqual(cancelled.status_code, 200)
            self.assertEqual(cancelled.json()["status"], "cancelled")
            cannot_cancel = client.post(
                f"/api/orders/{order_id}/cancel", headers=user_headers
            )
            self.assertEqual(cannot_cancel.status_code, 409)

            completed_order = client.post(
                "/api/orders",
                json={"items": [{"recipe_id": active_id, "quantity": 1}]},
                headers=user_headers,
            )
            self.assertEqual(completed_order.status_code, 200)
            completed_id = completed_order.json()["id"]
            user_status_update = client.put(
                f"/api/admin/orders/{completed_id}/status",
                json={"status": "completed"},
                headers=user_headers,
            )
            self.assertEqual(user_status_update.status_code, 403)
            invalid_status = client.put(
                f"/api/admin/orders/{completed_id}/status",
                json={"status": "confirmed"},
                headers=admin_headers,
            )
            self.assertEqual(invalid_status.status_code, 422)
            completed_update = client.put(
                f"/api/admin/orders/{completed_id}/status",
                json={"status": "completed"},
                headers=admin_headers,
            )
            self.assertEqual(completed_update.status_code, 200)
            self.assertEqual(completed_update.json()["status"], "completed")
            completed_filter = client.get(
                "/api/admin/orders?status=completed", headers=admin_headers
            )
            self.assertEqual(completed_filter.status_code, 200)
            self.assertIn(
                completed_id, [item["id"] for item in completed_filter.json()]
            )
            completed_cancel = client.post(
                f"/api/orders/{completed_id}/cancel", headers=user_headers
            )
            self.assertEqual(completed_cancel.status_code, 409)
            completed_status_change = client.put(
                f"/api/admin/orders/{completed_id}/status",
                json={"status": "cancelled"},
                headers=admin_headers,
            )
            self.assertEqual(completed_status_change.status_code, 409)
            print("order_validation_and_rollback=passed")
            print("order_price_snapshot=passed")
            print("order_user_isolation=passed")
            print("order_cancel_rules=passed")
            print("admin_order_permissions_and_status=passed")
        finally:
            setup_conn.close()
            cleanup_conn = get_connection()
            try:
                with cleanup_conn.transaction():
                    with cleanup_conn.cursor() as cursor:
                        cursor.execute("DELETE FROM orders WHERE user_id IN (SELECT id FROM users WHERE username IN (%s, %s, %s))", (admin_username, user_username, other_username))
                        if active_id is not None or inactive_id is not None:
                            cursor.execute("DELETE FROM recipes WHERE id IN (%s, %s)", (active_id, inactive_id))
                        if category_id is not None:
                            cursor.execute("DELETE FROM recipe_categories WHERE id = %s", (category_id,))
                        cursor.execute("DELETE FROM users WHERE username IN (%s, %s, %s)", (admin_username, user_username, other_username))
            finally:
                cleanup_conn.close()


if __name__ == "__main__":
    unittest.main()
