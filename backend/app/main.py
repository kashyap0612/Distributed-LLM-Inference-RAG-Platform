from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.cache.redis_cache import cache
from app.middleware.request_context import RequestContextMiddleware
from app.observability.logging import configure_logging

configure_logging()
app = FastAPI(title="Distributed LLM Inference + RAG Platform", version="0.1.0")
app.add_middleware(RequestContextMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

@app.on_event("startup")
async def startup(): await cache.connect()
