from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.orchestrator import Agent, AgentOrchestrator, Evidence, RuleBasedAgent
from app.agents.tools import create_agent_tools
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.services.embeddings import EmbeddingService, get_embedding_service


class AgentAskRequest(BaseModel):
	query: str = Field(min_length=1, max_length=200)


class AgentEvidenceResponse(BaseModel):
	item_id: int
	source_item_id: str
	title: str | None
	summary: str | None
	source: str
	tool_name: str
	relevance_score: float | None


class AgentAskResponse(BaseModel):
	query: str
	answer: str
	evidence: list[AgentEvidenceResponse]
	tool_iterations: int
	stop_reason: str


def get_agent() -> Agent:
	return RuleBasedAgent()


router = APIRouter(tags=["agent"])


@router.post("/ask", response_model=AgentAskResponse)
def ask_knowledge_agent(
	request: AgentAskRequest,
	db: Session = Depends(get_db),
	embedding_service: EmbeddingService = Depends(get_embedding_service),
	agent: Agent = Depends(get_agent),
	current_user: User = Depends(get_current_user),
) -> AgentAskResponse:
	query = request.query.strip()
	tools = create_agent_tools(db, embedding_service, owner_id=current_user.id)
	result = AgentOrchestrator(agent, tools, max_tool_iterations=3).run(query)
	return AgentAskResponse(
		query=query,
		answer=result.answer,
		evidence=[AgentEvidenceResponse(**item.__dict__) for item in result.evidence],
		tool_iterations=result.tool_iterations,
		stop_reason=result.stop_reason,
	)
