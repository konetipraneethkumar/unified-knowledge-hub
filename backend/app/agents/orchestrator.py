import re
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class Evidence:
	item_id: int
	source_item_id: str
	title: str | None
	summary: str | None
	source: str
	tool_name: str
	relevance_score: float | None = None


@dataclass(frozen=True)
class ToolCall:
	name: str
	query: str | None = None
	item_id: int | None = None


class Agent(Protocol):
	def choose_tool(
		self,
		query: str,
		evidence: Sequence[Evidence],
		available_tools: Sequence[str],
		called_tools: Sequence[str],
	) -> ToolCall | None: ...

	def formulate_answer(
		self, query: str, evidence: Sequence[Evidence]
	) -> str: ...


@dataclass(frozen=True)
class AgentResult:
	answer: str
	evidence: list[Evidence]
	tool_iterations: int
	stop_reason: str


class RuleBasedAgent:
	"""Small no-LLM default; replace with a model-backed Agent when available."""

	_item_id_pattern = re.compile(
		r"(?:knowledge\s+item|item|id)\s*#?\s*(\d+)|#(\d+)",
		re.IGNORECASE,
	)

	def choose_tool(
		self,
		query: str,
		evidence: Sequence[Evidence],
		available_tools: Sequence[str],
		called_tools: Sequence[str],
	) -> ToolCall | None:
		id_match = self._item_id_pattern.search(query)
		if id_match and "knowledge_item_lookup" not in called_tools:
			item_id = int(id_match.group(1) or id_match.group(2))
			if "knowledge_item_lookup" in available_tools:
				return ToolCall(name="knowledge_item_lookup", item_id=item_id)

		keyword_cues = ("exact", "keyword", "title", "contains")
		tool_name = (
			"local_search"
			if any(cue in query.lower() for cue in keyword_cues)
			else "hybrid_search"
		)
		if tool_name in available_tools and tool_name not in called_tools:
			return ToolCall(name=tool_name, query=query)
		return None

	def formulate_answer(
		self, query: str, evidence: Sequence[Evidence]
	) -> str:
		if not evidence:
			return f"I couldn't find supporting knowledge items for: {query}"
		return f"Found {len(evidence)} supporting knowledge item(s) for: {query}"


class AgentOrchestrator:
	def __init__(
		self,
		agent: Agent,
		tools: dict[str, object],
		*,
		max_tool_iterations: int = 3,
	):
		if max_tool_iterations < 1:
			raise ValueError("max_tool_iterations must be positive")
		self.agent = agent
		self.tools = tools
		self.max_tool_iterations = max_tool_iterations

	def run(self, query: str) -> AgentResult:
		evidence: list[Evidence] = []
		called_tools: list[str] = []
		stop_reason = "agent_finished"

		while True:
			tool_call = self.agent.choose_tool(
				query=query,
				evidence=tuple(evidence),
				available_tools=tuple(self.tools),
				called_tools=tuple(called_tools),
			)
			if tool_call is None:
				break
			if tool_call.name not in self.tools:
				stop_reason = "unknown_tool"
				break
			if tool_call.name in called_tools:
				stop_reason = "repeated_tool"
				break
			if len(called_tools) >= self.max_tool_iterations:
				stop_reason = "iteration_limit"
				break

			called_tools.append(tool_call.name)
			tool = self.tools[tool_call.name]
			if not callable(tool):
				raise TypeError(f"Tool {tool_call.name!r} is not callable")
			tool_evidence = tool(tool_call)
			evidence.extend(tool_evidence)

		unique_evidence = _deduplicate_evidence(evidence)
		return AgentResult(
			answer=self.agent.formulate_answer(query, tuple(unique_evidence)),
			evidence=unique_evidence,
			tool_iterations=len(called_tools),
			stop_reason=stop_reason,
		)


def _deduplicate_evidence(evidence: Sequence[Evidence]) -> list[Evidence]:
	unique_by_id: dict[int, Evidence] = {}
	for candidate in evidence:
		current = unique_by_id.get(candidate.item_id)
		if current is None or _evidence_score(candidate) > _evidence_score(current):
			unique_by_id[candidate.item_id] = candidate
	return list(unique_by_id.values())


def _evidence_score(evidence: Evidence) -> float:
	return evidence.relevance_score if evidence.relevance_score is not None else 0.0