import unittest

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.core.security import get_current_user
from app.main import app
from app.models import ConnectorSyncActivity, SearchHistory, User
from _postgres_test_db import create_postgres_test_engine


class ActivityApiTests(unittest.TestCase):
    def setUp(self):
        self.engine, self.cleanup_database = create_postgres_test_engine()
        self.session_factory = sessionmaker(bind=self.engine)
        db = self.session_factory()
        db.add_all(
            [
                User(id=7, email="owner@example.invalid", password_hash="test"),
                User(id=8, email="other@example.invalid", password_hash="test"),
            ]
        )
        db.commit()
        db.add(
            SearchHistory(
                owner_id=8,
                query="private query",
                mode="ask",
                result_count=1,
                source_count=1,
            )
        )
        db.add(
            ConnectorSyncActivity(
                owner_id=7,
                connector_id=None,
                connector_name="Google Drive",
                connector_type="GOOGLE_DRIVE",
                status="completed_with_errors",
                processed=2,
                skipped=1,
                failed=1,
                deleted=0,
            )
        )
        db.commit()
        db.close()

        def override_get_db():
            db = self.session_factory()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: User(
            id=7, email="owner@example.invalid", password_hash="test"
        )
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        self.cleanup_database()

    def test_search_history_is_owner_scoped_and_clearable(self):
        created = self.client.post(
            "/api/v1/activity/search-history",
            json={"query": "  project report  ", "mode": "search", "result_count": 3, "source_count": 2},
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["query"], "project report")
        self.assertEqual(created.json()["mode"], "search")
        self.assertEqual(created.json()["result_count"], 3)
        history = self.client.get("/api/v1/activity/search-history")
        self.assertEqual(history.status_code, 200)
        self.assertEqual([entry["query"] for entry in history.json()], ["project report"])
        self.assertEqual(self.client.delete("/api/v1/activity/search-history").status_code, 204)
        self.assertEqual(self.client.get("/api/v1/activity/search-history").json(), [])

    def test_sync_history_returns_persisted_counts_for_current_user(self):
        response = self.client.get("/api/v1/activity/sync")
        self.assertEqual(response.status_code, 200)
        event = response.json()[0]
        self.assertEqual(event["connector_name"], "Google Drive")
        self.assertEqual(event["connector_type"], "GOOGLE_DRIVE")
        self.assertEqual(event["status"], "completed_with_errors")
        self.assertEqual(event["processed"], 2)
        self.assertEqual(event["skipped"], 1)
        self.assertEqual(event["failed"], 1)
        self.assertEqual(event["deleted"], 0)


if __name__ == "__main__":
    unittest.main()
