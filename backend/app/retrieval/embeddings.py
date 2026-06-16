import hashlib, numpy as np

class EmbeddingService:
    dim = 384
    async def embed(self, text: str) -> list[float]:
        # Deterministic hashing keeps local development cheap while preserving vector-search behavior.
        vec = np.zeros(self.dim, dtype=np.float32)
        for token in text.lower().split():
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        norm = np.linalg.norm(vec) or 1.0
        return (vec / norm).tolist()

embeddings = EmbeddingService()
