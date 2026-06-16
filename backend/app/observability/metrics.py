from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_LATENCY = Histogram("http_request_latency_seconds", "HTTP latency", ["route", "method"], buckets=(.01,.05,.1,.25,.5,1,2,5,10))
ACTIVE_REQUESTS = Gauge("active_requests", "Active HTTP requests")
ACTIVE_STREAMS = Gauge("active_streams", "Active SSE streams")
TOKENS = Counter("generated_tokens_total", "Generated tokens", ["model"])
CACHE = Counter("cache_events_total", "Cache events", ["layer", "result"])
RETRIEVAL_LATENCY = Histogram("retrieval_latency_seconds", "Vector retrieval latency", buckets=(.005,.01,.025,.05,.1,.25,.5,1,2))
ROUTING = Counter("model_routing_total", "Routing decisions", ["model", "reason"])
STREAM_DURATION = Histogram("stream_duration_seconds", "SSE stream duration")

def metrics_response() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
