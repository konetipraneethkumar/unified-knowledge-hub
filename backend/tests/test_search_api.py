import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import KnowledgeItem


class KnowledgeItemSearchApiTests(unittest.TestCase):
	def setUp(self):
		self.engine = create_engine(
			"sqlite://",
			connect_args={"check_same_thread": False},
			poolclass=StaticPool,
		)
		Base.metadata.create_all(self.engine)
		self.session_factory = sessionmaker(bind=self.engine)

		def override_get_db():
			db = self.session_factory()
			try:
				yield db
			finally:
				db.close()

		app.dependency_overrides[get_db] = override_get_db
		self.client = TestClient(app)

		# Search results are scoped to the authenticated user, so create a real
		# test principal and use its bearer token in all API requests.
		auth_response = self.client.post(
			"/auth/register",
			json={
				"email": "search-api-test@example.com",
				"password": "test-password-for-api",
			},
		)
		self.assertEqual(auth_response.status_code, 201, auth_response.text)
		self.user_id = auth_response.json()["user"]["id"]
		self.client.headers.update(
			{"Authorization": f"Bearer {auth_response.json()['access_token']}"}
		)

	def tearDown(self):
		self.client.close()
		app.dependency_overrides.pop(get_db, None)
		Base.metadata.drop_all(self.engine)
		self.engine.dispose()

	def create_item(
		self,
		source_item_id: str,
		*,
		title: str | None = None,
		summary: str | None = None,
		source: str = "local",
		item_type: str | None = None,
	):
		return self.client.post(
			"/knowledge-items",
			json={
				"source": source,
				"source_item_id": source_item_id,
				"title": title,
				"summary": summary,
				"item_type": item_type,
			},
		)

	def test_search_matches_all_requested_fields_case_insensitively(self):
		for source_item_id, kwargs in (
			("title-1", {"title": "Annual PLAN", "summary": "Roadmap", "item_type": "file"}),
			("summary-1", {"title": "Notes", "summary": "Quarterly planning", "item_type": "file"}),
			("source-1", {"title": "Notes", "source": "Quarterly Archive", "item_type": "file"}),
			("type-1", {"title": "Notes", "source": "local", "item_type": "Quarterly report"}),
		):
			response = self.create_item(source_item_id, **kwargs)
			self.assertEqual(response.status_code, 201, response.text)

		for query, expected_source_item_id in (
			("annual", "title-1"),
			("PLANNING", "summary-1"),
			("archive", "source-1"),
			("REPORT", "type-1"),
		):
			with self.subTest(query=query):
				response = self.client.get("/search", params={"q": query})
				self.assertEqual(response.status_code, 200)
				payload = response.json()
				self.assertEqual(payload["query"], query)
				self.assertEqual(payload["total"], 1)
				self.assertEqual(
					payload["items"][0]["source_item_id"],
					expected_source_item_id,
				)

	def test_search_matches_extracted_document_content(self):
		db = self.session_factory()
		try:
			db.add(
				KnowledgeItem(
					source="local",
					source_item_id="document-content",
					title="Notes",
					item_type="file",
					content="A distinctive searchable paragraph",
					processing_status="processed",
					owner_id=self.user_id,
				)
			)
			db.commit()
		finally:
			db.close()

		response = self.client.get("/search", params={"q": "distinctive searchable"})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["total"], 1)
		self.assertEqual(
			response.json()["items"][0]["source_item_id"], "document-content"
		)

	def test_search_returns_title_matches_first_and_paginates(self):
		self.create_item("summary-first", title="Notes", summary="Project report")
		self.create_item("title-first", title="Project report")
		self.create_item("title-second", title="Project report follow-up")

		response = self.client.get(
			"/search", params={"q": "project report", "offset": 1, "limit": 1}
		)

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["offset"], 1)
		self.assertEqual(payload["limit"], 1)
		self.assertEqual(payload["total"], 3)
		self.assertEqual(len(payload["items"]), 1)
		self.assertEqual(payload["items"][0]["source_item_id"], "title-second")

	def test_search_ranks_exact_and_strong_title_matches_before_summaries(self):
		self.create_item("summary-exact", title="Notes", summary="Research plan")
		self.create_item("title-substring-first", title="A research plan overview")
		self.create_item("title-substring-second", title="Another research plan")
		self.create_item("title-prefix", title="Research plan for launch")
		self.create_item("title-exact", title="Research plan")

		response = self.client.get("/search", params={"q": "research plan"})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(
			[item["source_item_id"] for item in response.json()["items"]],
			[
				"title-exact",
				"title-prefix",
				"title-substring-first",
				"title-substring-second",
				"summary-exact",
			],
		)

	def test_search_ranks_summary_matches_by_strength(self):
		self.create_item("summary-substring", title="Notes", summary="Notes on quarterly review")
		self.create_item("summary-prefix", title="Archive", summary="Quarterly review notes")
		self.create_item("summary-exact", title="Report", summary="Quarterly review")

		response = self.client.get("/search", params={"q": "quarterly review"})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(
			[item["source_item_id"] for item in response.json()["items"]],
			["summary-exact", "summary-prefix", "summary-substring"],
		)

	def test_search_treats_wildcards_as_literal_text(self):
		self.create_item("percent", title="Literal % sign")
		self.create_item("ordinary", title="Other title")

		response = self.client.get("/search", params={"q": "%"})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["total"], 1)
		self.assertEqual(response.json()["items"][0]["source_item_id"], "percent")

		injection_response = self.client.get(
			"/search", params={"q": "' OR 1=1 --"}
		)
		self.assertEqual(injection_response.status_code, 200)
		self.assertEqual(injection_response.json()["total"], 0)

	def test_search_validates_query_and_pagination(self):
		for params in (
			{},
			{"q": "   "},
			{"q": "valid", "limit": 101},
			{"q": "valid", "offset": -1},
		):
			with self.subTest(params=params):
				response = self.client.get("/search", params=params)
				self.assertEqual(response.status_code, 422)

	def test_hybrid_search_returns_scored_results(self):
		self.create_item("hybrid-item", title="Hybrid retrieval notes")

		response = self.client.get(
			"/hybrid-search", params={"q": "hybrid retrieval"}
		)

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["query"], "hybrid retrieval")
		self.assertEqual(payload["total"], 1)
		self.assertEqual(
			payload["items"][0]["item"]["source_item_id"], "hybrid-item"
		)
		self.assertGreater(payload["items"][0]["relevance_score"], 0)


if __name__ == "__main__":
	unittest.main()
