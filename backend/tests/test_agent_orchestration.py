import unittest

from app.agents.orchestrator import (
	AgentOrchestrator,
	Evidence,
	ToolCall,
)


def evidence(item_id: int, tool_name: str, score: float) -> Evidence:
	return Evidence(
		item_id=item_id,
		source_item_id=f"source-{item_id}",
		title=f"Item {item_id}",
		summary="Evidence summary",
		source="local",
		tool_name=tool_name,
		relevance_score=score,
	)


class MockAgent:
	def __init__(self, calls: list[ToolCall | None]):
		self.calls = list(calls)
		self.observed_inputs = []

	def choose_tool(
		self, query, evidence, available_tools, called_tools
	) -> ToolCall | None:
		self.observed_inputs.append(
			(query, evidence, available_tools, called_tools)
		)
		if self.calls:
			return self.calls.pop(0)
		return None

	def formulate_answer(self, query, evidence) -> str:
		return f"Answer based on {len(evidence)} item(s) for {query}"


class AgentOrchestrationTests(unittest.TestCase):
	def test_agent_selects_tools_and_returns_deduplicated_evidence(self):
		agent = MockAgent(
			[
				ToolCall("local_search", query="planning"),
				ToolCall("knowledge_item_lookup", item_id=7),
				None,
			]
		)
		tool_calls = []

		def local_search(call):
			tool_calls.append(call)
			return [evidence(7, "local_search", 0.5)]

		def lookup(call):
			tool_calls.append(call)
			return [
				evidence(7, "knowledge_item_lookup", 1.0),
				evidence(8, "knowledge_item_lookup", 1.0),
			]

		result = AgentOrchestrator(
			agent,
			{"local_search": local_search, "knowledge_item_lookup": lookup},
		).run("planning")

		self.assertEqual([call.name for call in tool_calls], [
			"local_search",
			"knowledge_item_lookup",
		])
		self.assertEqual(result.tool_iterations, 2)
		self.assertEqual(result.stop_reason, "agent_finished")
		self.assertEqual([item.item_id for item in result.evidence], [7, 8])
		self.assertEqual(result.evidence[0].tool_name, "knowledge_item_lookup")
		self.assertIn("2 item(s)", result.answer)
		self.assertEqual(
			agent.observed_inputs[0],
			(
				"planning",
				(),
				("local_search", "knowledge_item_lookup"),
				(),
			),
		)

	def test_repeated_tool_call_stops_without_invoking_tool_twice(self):
		agent = MockAgent(
			[
				ToolCall("local_search", query="notes"),
				ToolCall("local_search", query="notes"),
			]
		)
		invocations = []
		orchestrator = AgentOrchestrator(
			agent,
			{"local_search": lambda call: invocations.append(call) or []},
		)

		result = orchestrator.run("notes")

		self.assertEqual(len(invocations), 1)
		self.assertEqual(result.tool_iterations, 1)
		self.assertEqual(result.stop_reason, "repeated_tool")

	def test_unknown_tool_stops_and_iteration_limit_is_enforced(self):
		unknown_agent = MockAgent([ToolCall("not_registered")])
		unknown_result = AgentOrchestrator(
			unknown_agent,
			{"local_search": lambda call: []},
		).run("query")
		self.assertEqual(unknown_result.stop_reason, "unknown_tool")
		self.assertEqual(unknown_result.tool_iterations, 0)

		calls = [
			ToolCall("tool_one"),
			ToolCall("tool_two"),
			ToolCall("tool_three"),
		]
		limited_agent = MockAgent(calls)
		invocations = []
		tools = {
			name: lambda call, name=name: invocations.append(name) or []
			for name in ("tool_one", "tool_two", "tool_three")
		}
		limited_result = AgentOrchestrator(
			limited_agent, tools, max_tool_iterations=2
		).run("query")

		self.assertEqual(invocations, ["tool_one", "tool_two"])
		self.assertEqual(limited_result.tool_iterations, 2)
		self.assertEqual(limited_result.stop_reason, "iteration_limit")


if __name__ == "__main__":
	unittest.main()