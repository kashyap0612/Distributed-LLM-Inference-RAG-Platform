from pydantic import BaseModel, Field
from typing import Any

class ChatRequest(BaseModel):
    message: str
    use_rag: bool = True
    top_k: int = Field(default=4, ge=1, le=12)
    model_hint: str | None = None

class RetrievedChunk(BaseModel):
    text: str
    score: float
    source: str
    chunk_id: str

class RouteDecision(BaseModel):
    model: str
    confidence: float
    complexity: float
    reasons: list[str]

class TraceEvent(BaseModel):
    stage: str
    status: str
    detail: dict[str, Any] = {}

class ChatResponse(BaseModel):
    answer: str
    route: RouteDecision
    retrieved_chunks: list[RetrievedChunk]
    latency_ms: float
    trace: list[TraceEvent]
