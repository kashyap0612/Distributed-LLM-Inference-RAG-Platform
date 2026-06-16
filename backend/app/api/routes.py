import json, time
from fastapi import APIRouter, UploadFile, File, Request, Response
from fastapi.responses import StreamingResponse
from pypdf import PdfReader
from io import BytesIO
from app.cache.redis_cache import cache
from app.models.schemas import ChatRequest, ChatResponse
from app.routing.router import InferenceRouter
from app.retrieval.rag import rag
from app.services.inference import inference, failure_modes
from app.services.rate_limit import enforce_rate_limit
from app.observability.metrics import metrics_response, ACTIVE_STREAMS, TOKENS, STREAM_DURATION

router = APIRouter(); model_router = InferenceRouter()

@router.get("/health")
async def health(): return {"status":"ok", "redis_degraded": cache.force_down, "model_crash": failure_modes.model_crash, "timeout": failure_modes.timeout}

@router.get("/metrics")
def metrics():
    body, media = metrics_response(); return Response(body, media_type=media)

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    await enforce_rate_limit(request.client.host if request.client else "unknown"); start=time.perf_counter(); trace=[]
    cached = await cache.get_json("response", req.model_dump_json())
    if cached: return ChatResponse(**cached)
    chunks = await rag.retrieve(req.message, req.top_k) if req.use_rag else []
    trace.append({"stage":"retrieval","status":"complete","detail":{"chunks":len(chunks)}})
    decision = model_router.decide(req.message, req.model_hint)
    context = "\n".join(c.text for c in chunks)
    try: answer = await inference.complete(f"Context:\n{context}\nQuestion:{req.message}", decision.model)
    except Exception as exc:
        trace.append({"stage":"fallback","status":"activated","detail":{"error":str(exc)}})
        answer = "Degraded response: primary model path failed, returning retrieved context summary. " + context[:500]
    data = ChatResponse(answer=answer, route=decision, retrieved_chunks=chunks, latency_ms=(time.perf_counter()-start)*1000, trace=trace)
    await cache.set_json("response", req.model_dump_json(), data.model_dump())
    return data

@router.get("/stream")
async def stream(message: str, request: Request, top_k: int = 4, use_rag: bool = True, model_hint: str | None = None):
    await enforce_rate_limit(request.client.host if request.client else "unknown")
    async def events():
        ACTIVE_STREAMS.inc(); start=time.perf_counter(); token_count=0
        try:
            yield f"event: trace\ndata: {json.dumps({'stage':'accepted','status':'ok'})}\n\n"
            chunks = await rag.retrieve(message, top_k) if use_rag else []
            yield f"event: retrieval\ndata: {json.dumps([c.model_dump() for c in chunks])}\n\n"
            decision = model_router.decide(message, model_hint)
            yield f"event: route\ndata: {decision.model_dump_json()}\n\n"
            prompt = "\n".join(c.text for c in chunks) + "\nQuestion:" + message
            try:
                async for token in inference.stream(prompt, decision.model):
                    token_count += 1; TOKENS.labels(decision.model).inc()
                    yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
            except Exception as exc:
                yield f"event: fallback\ndata: {json.dumps({'error': str(exc), 'message': 'degraded mode activated'})}\n\n"
            yield f"event: done\ndata: {json.dumps({'tokens': token_count, 'duration_ms': (time.perf_counter()-start)*1000})}\n\n"
        finally:
            STREAM_DURATION.observe(time.perf_counter()-start); ACTIVE_STREAMS.dec()
    return StreamingResponse(events(), media_type="text/event-stream")

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    raw = await file.read()
    if file.filename and file.filename.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(raw)); text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else: text = raw.decode("utf-8", errors="ignore")
    chunks = await rag.ingest(text, file.filename or "upload")
    return {"source": file.filename, "chunks_indexed": chunks}

@router.post("/retrieve")
async def retrieve(req: ChatRequest): return {"chunks": [c.model_dump() for c in await rag.retrieve(req.message, req.top_k)]}

@router.get("/routing-debug")
async def routing_debug(message: str, model_hint: str | None = None): return model_router.decide(message, model_hint)

@router.post("/simulate/{failure}")
async def simulate(failure: str):
    if failure == "clear": cache.force_down=False; failure_modes.model_crash=False; failure_modes.timeout=False
    if failure == "redis_failure": cache.force_down=True
    if failure == "model_crash": failure_modes.model_crash=True
    if failure == "timeout": failure_modes.timeout=True
    return await health()
