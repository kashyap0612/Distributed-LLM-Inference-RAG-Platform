import asyncio, httpx
from collections.abc import AsyncIterator
from app.core.config import settings

class FailureModes:
    model_crash = False
    timeout = False

failure_modes = FailureModes()

class InferenceService:
    async def complete(self, prompt: str, model: str) -> str:
        chunks = []
        async for token in self.stream(prompt, model): chunks.append(token)
        return "".join(chunks)

    async def stream(self, prompt: str, model: str) -> AsyncIterator[str]:
        if failure_modes.model_crash: raise RuntimeError("simulated model crash")
        if failure_modes.timeout: await asyncio.sleep(3); raise TimeoutError("simulated model timeout")
        endpoint = settings.vllm_large_url if model == "large" else settings.vllm_small_url
        if endpoint:
            async with httpx.AsyncClient(timeout=30) as client:
                async with client.stream("POST", endpoint, json={"prompt": prompt, "stream": True}) as resp:
                    async for line in resp.aiter_text():
                        if line: yield line
            return
        answer = f"[{model} simulated] Based on the retrieved context and routing policy, {prompt[:320]}"
        for word in answer.split():
            await asyncio.sleep(0.025 if model == "small" else 0.045)
            yield word + " "

inference = InferenceService()
