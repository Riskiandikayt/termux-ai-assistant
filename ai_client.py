import asyncio
import json
import sys
import httpx
from typing import AsyncGenerator, Optional
import config


class AIClient:
    def __init__(self, backend: str = None):
        self.backend = backend or config.AI_BACKEND

    async def chat_stream(self, prompt: str, system: str = None) -> AsyncGenerator[str, None]:
        if self.backend == "llamacpp":
            async for token in self._llamacpp_stream(prompt, system):
                yield token
        elif self.backend == "ollama":
            async for token in self._ollama_stream(prompt, system):
                yield token
        else:
            yield f"[ERROR] Backend tidak dikenal: {self.backend}"

    async def chat(self, prompt: str, system: str = None) -> str:
        result = []
        async for token in self.chat_stream(prompt, system):
            result.append(token)
        return "".join(result)

    async def _llamacpp_stream(self, prompt: str, system: str = None) -> AsyncGenerator[str, None]:
        url = f"{config.LLAMACPP_HOST}/v1/chat/completions"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "max_tokens": config.MAX_TOKENS,
            "temperature": config.TEMPERATURE,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, json=payload) as resp:
                    if resp.status_code != 200:
                        yield f"[ERROR] llama.cpp server merespons {resp.status_code}. Pastikan server sudah berjalan."
                        return
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                obj = json.loads(data)
                                delta = obj["choices"][0]["delta"].get("content", "")
                                if delta:
                                    yield delta
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
        except httpx.ConnectError:
            yield (
                "\n[ERROR] Tidak bisa terhubung ke llama.cpp server.\n"
                "Jalankan server dulu dengan:\n"
                "  ./llama-server -m models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf --host 127.0.0.1 --port 8080\n"
            )
        except Exception as e:
            yield f"\n[ERROR] {type(e).__name__}: {e}\n"

    async def _ollama_stream(self, prompt: str, system: str = None) -> AsyncGenerator[str, None]:
        url = f"{config.OLLAMA_HOST}/api/chat"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": config.OLLAMA_MODEL,
            "messages": messages,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, json=payload) as resp:
                    if resp.status_code != 200:
                        yield f"[ERROR] Ollama merespons {resp.status_code}. Pastikan Ollama sudah berjalan."
                        return
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            obj = json.loads(line)
                            delta = obj.get("message", {}).get("content", "")
                            if delta:
                                yield delta
                            if obj.get("done"):
                                break
                        except (json.JSONDecodeError, KeyError):
                            continue
        except httpx.ConnectError:
            yield (
                "\n[ERROR] Tidak bisa terhubung ke Ollama.\n"
                "Jalankan Ollama dulu dengan:\n"
                "  ollama serve\n"
                "Lalu pull model:\n"
                f"  ollama pull {config.OLLAMA_MODEL}\n"
            )
        except Exception as e:
            yield f"\n[ERROR] {type(e).__name__}: {e}\n"

    async def is_server_ready(self) -> bool:
        if self.backend == "llamacpp":
            url = f"{config.LLAMACPP_HOST}/health"
        elif self.backend == "ollama":
            url = f"{config.OLLAMA_HOST}/api/tags"
        else:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                return resp.status_code == 200
        except Exception:
            return False
