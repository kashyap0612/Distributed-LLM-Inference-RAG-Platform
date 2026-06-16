from app.models.schemas import RouteDecision
from app.observability.metrics import ROUTING

class InferenceRouter:
    def decide(self, message: str, model_hint: str | None = None) -> RouteDecision:
        words = message.split(); reasons = []
        complexity = min(1.0, len(words) / 80)
        hard_terms = ("architecture", "prove", "optimize", "distributed", "debug", "tradeoff", "benchmark")
        hits = [t for t in hard_terms if t in message.lower()]
        if hits:
            complexity = min(1.0, complexity + 0.35); reasons.append(f"systems terms: {', '.join(hits[:3])}")
        if "?" in message and len(words) < 18:
            complexity -= 0.15; reasons.append("short direct question")
        if model_hint in {"small", "large"}:
            model = model_hint; reasons.append("user model hint")
        else:
            model = "large" if complexity >= 0.45 else "small"
        confidence = 0.55 + abs(complexity - 0.45)
        ROUTING.labels(model, reasons[0] if reasons else "complexity_threshold").inc()
        return RouteDecision(model=model, confidence=round(min(confidence, .99), 2), complexity=round(max(complexity, 0), 2), reasons=reasons or ["complexity threshold"])
