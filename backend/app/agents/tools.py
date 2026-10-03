from collections.abc import Callable

from sqlalchemy.orm import Session

from app.agents.orchestrator import Evidence, ToolCall
from app.services.embeddings import EmbeddingService
from app.services.knowledge_items import (
	get_knowledge_item,
	search_knowledge_items,
)
from app.retrieval.hybrid import hybrid_search as run_hybrid_search


AgentTool = Callable[[ToolCall], list[Evidence]]


def local_search_tool(
	db: Session, query: str, *, limit: int = 10, owner_id: int | None = None
) -> list[Evidence]:
	items, _total = search_knowledge_items(db, query=query, limit=limit, owner_id=owner_id)
	return [
		_evidence(item, "local_search", relevance_score=1.0 / rank)
		for rank, item in enumerate(items, start=1)
	]


def hybrid_search_tool(
	db: Session,
	query: str,
	embedding_service: EmbeddingService,
	*,
	limit: int = 10,
	owner_id: int | None = None,
) -> list[Evidence]:
	results = run_hybrid_search(
		db,
		query=query,
		embedding_service=embedding_service,
		limit=limit,
		owner_id=owner_id,
	)
	return [
		_evidence(
			result.item,
			"hybrid_search",
			relevance_score=result.relevance_score,
		)
		for result in results
	]


def knowledge_item_lookup_tool(
	db: Session, item_id: int, *, owner_id: int | None = None
) -> list[Evidence]:
	item = get_knowledge_item(db, item_id, owner_id)
	if item is None:
		return []
	return [_evidence(item, "knowledge_item_lookup", relevance_score=1.0)]


def create_agent_tools(
	db: Session,
	embedding_service: EmbeddingService,
	*,
	limit: int = 10,
	owner_id: int | None = None,
) -> dict[str, AgentTool]:
	def local_search(call: ToolCall) -> list[Evidence]:
		if not call.query:
			raise ValueError("local_search requires a query")
		return local_search_tool(db, call.query, limit=limit, owner_id=owner_id)

	def hybrid_search(call: ToolCall) -> list[Evidence]:
		if not call.query:
			raise ValueError("hybrid_search requires a query")
		return hybrid_search_tool(
			db, call.query, embedding_service, limit=limit, owner_id=owner_id
		)

	def knowledge_item_lookup(call: ToolCall) -> list[Evidence]:
		if call.item_id is None:
			raise ValueError("knowledge_item_lookup requires an item ID")
		return knowledge_item_lookup_tool(db, call.item_id, owner_id=owner_id)

	return {
		"local_search": local_search,
		"hybrid_search": hybrid_search,
		"knowledge_item_lookup": knowledge_item_lookup,
	}


def _evidence(item, tool_name: str, relevance_score: float) -> Evidence:
	return Evidence(
		item_id=item.id,
		source_item_id=item.source_item_id,
		title=item.title,
		summary=item.summary,
		source=item.source,
		tool_name=tool_name,
		relevance_score=relevance_score,
	)
