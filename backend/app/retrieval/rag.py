import time, uuid
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings
from app.models.schemas import RetrievedChunk
from app.retrieval.embeddings import embeddings
from app.observability.metrics import RETRIEVAL_LATENCY

class RAGService:
    def __init__(self): self.client = AsyncQdrantClient(url=settings.qdrant_url)
    async def ensure_collection(self):
        names = [c.name for c in (await self.client.get_collections()).collections]
        if settings.qdrant_collection not in names:
            await self.client.create_collection(settings.qdrant_collection, vectors_config=VectorParams(size=embeddings.dim, distance=Distance.COSINE))
    def chunk(self, text: str, size: int = 900, overlap: int = 120) -> list[str]:
        chunks=[]; start=0
        while start < len(text):
            chunks.append(text[start:start+size]); start += size-overlap
        return chunks
    async def ingest(self, text: str, source: str) -> int:
        await self.ensure_collection(); points=[]
        for i, chunk in enumerate(self.chunk(text)):
            points.append(PointStruct(id=str(uuid.uuid4()), vector=await embeddings.embed(chunk), payload={"text": chunk, "source": source, "chunk_id": f"{source}:{i}"}))
        if points: await self.client.upsert(settings.qdrant_collection, points)
        return len(points)
    async def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        await self.ensure_collection(); start=time.perf_counter()
        results = await self.client.search(settings.qdrant_collection, query_vector=await embeddings.embed(query), limit=top_k, with_payload=True)
        RETRIEVAL_LATENCY.observe(time.perf_counter()-start)
        return [RetrievedChunk(text=r.payload.get("text",""), source=r.payload.get("source","unknown"), chunk_id=r.payload.get("chunk_id", str(r.id)), score=float(r.score)) for r in results]

rag = RAGService()
