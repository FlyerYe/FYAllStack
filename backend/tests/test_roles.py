import unittest

import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.auth import create_access_token
from app.core.config import settings
from app.core.security import CurrentUser, get_current_user, require_admin


class RoleSecurityTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()

        @self.app.get("/admin-only")
        def admin_only(
            current_user: CurrentUser = Depends(require_admin),
        ):
            return current_user

        self.client = TestClient(self.app)

    def test_access_token_contains_role(self):
        token = create_access_token(7, "admin")
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        self.assertEqual(payload["sub"], "7")
        self.assertEqual(payload["role"], "admin")
        self.assertIn("exp", payload)

    def test_get_current_user_returns_id_and_role(self):
        token = create_access_token(8, "user")

        current_user = get_current_user(token)

        self.assertEqual(current_user, {"user_id": 8, "role": "user"})

    def test_admin_can_access_admin_dependency(self):
        token = create_access_token(1, "admin")

        response = self.client.get(
            "/admin-only",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"user_id": 1, "role": "admin"})

    def test_user_receives_forbidden_from_admin_dependency(self):
        token = create_access_token(2, "user")

        response = self.client.get(
            "/admin-only",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 403)

    def test_missing_token_is_unauthorized(self):
        response = self.client.get("/admin-only")

        self.assertEqual(response.status_code, 401)

    def test_token_without_valid_role_is_rejected(self):
        token = jwt.encode(
            {
                "sub": "3",
                "role": "owner",
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        with self.assertRaisesRegex(Exception, "无效 Token"):
            get_current_user(token)


if __name__ == "__main__":
    unittest.main()
