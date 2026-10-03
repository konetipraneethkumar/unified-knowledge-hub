from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent import router as agent_router
from app.api.auth import router as auth_router
from app.api.connectors import router as connectors_router
from app.api.devices import router as devices_router
from app.api.knowledge_items import router as knowledge_items_router
from app.api.search import router as search_router
from app.core.config import settings

app = FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
	allow_credentials=True,
	allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
	allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(connectors_router)
app.include_router(knowledge_items_router)
app.include_router(search_router)
app.include_router(agent_router)


@app.get("/health")
def health_check() -> dict[str, str]:
	return {"status": "ok"}
