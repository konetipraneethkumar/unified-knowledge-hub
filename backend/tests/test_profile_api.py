from datetime import datetime, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.main import app


class ProfileApiTests(unittest.TestCase):
    def setUp(self):
        self.user = SimpleNamespace(
            id=7,
            email="owner@example.invalid",
            display_name="Before",
            avatar_url=None,
            is_active=True,
            is_verified=False,
            created_at=datetime.now(timezone.utc),
        )
        self.db = Mock()
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_active_user] = lambda: self.user
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_active_user, None)

    def test_update_profile_changes_authenticated_users_display_name(self):
        response = self.client.patch(
            "/api/v1/auth/me", json={"display_name": "  Updated name  "}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], 7)
        self.assertEqual(response.json()["display_name"], "Updated name")
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(self.user)

    def test_update_profile_rejects_unknown_fields(self):
        response = self.client.patch(
            "/api/v1/auth/me",
            json={"display_name": "Name", "email": "different@example.invalid"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.user.email, "owner@example.invalid")


if __name__ == "__main__":
    unittest.main()
