import time, uuid
import structlog.contextvars
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.observability.metrics import ACTIVE_REQUESTS, REQUEST_LATENCY

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)
        request.state.request_id = request_id
        ACTIVE_REQUESTS.inc(); start = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers["x-request-id"] = request_id
            return response
        finally:
            REQUEST_LATENCY.labels(request.url.path, request.method).observe(time.perf_counter() - start)
            ACTIVE_REQUESTS.dec(); structlog.contextvars.clear_contextvars()
