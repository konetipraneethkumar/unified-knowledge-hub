from fastapi import FastAPI

from app.api.knowledge_items import router as knowledge_items_router

app = FastAPI()
app.include_router(knowledge_items_router)


@app.get("/health")
def health_check() -> dict[str, str]:
	return {"status": "ok"}
