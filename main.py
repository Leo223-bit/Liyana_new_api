"""FastAPI backend for the Liyana 3.0 Android chat client."""

from __future__ import annotations

import logging
import os
from typing import Literal

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from requests import RequestException, Timeout

OLLAMA_CHAT_URL = "https://ollama.com/api/chat"
REQUEST_TIMEOUT_SECONDS = 60
logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="LIYANA-pro-API-v2",
    version="1.0.0",
    description="Chat API for the Liyana 3.0 Android client.",
)


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage] | None = Field(default=None, min_length=1)
    message: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def require_chat_content(self) -> "ChatRequest":
        if not self.messages and not self.message:
            raise ValueError("Provide a non-empty messages array or message string.")
        return self


class ChatResponse(BaseModel):
    response: str


@app.get("/health")
def health() -> dict[str, str]:
    """Return a secret-free process health response."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    """Send conversation history to Ollama Cloud and return Android-friendly JSON."""
    api_key = os.getenv("OLLAMA_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="Chat service is not configured.")

    messages = payload.messages or [ChatMessage(role="user", content=payload.message or "")]
    model = os.getenv("OLLAMA_MODEL", "beam:cloud").strip() or "beam:cloud"

    try:
        upstream = requests.post(
            OLLAMA_CHAT_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "model": model,
                "messages": [item.model_dump() for item in messages],
                "stream": False,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except Timeout:
        logger.warning("Ollama Cloud request timed out")
        raise HTTPException(status_code=504, detail="The chat service timed out.") from None
    except RequestException:
        logger.warning("Could not reach Ollama Cloud")
        raise HTTPException(status_code=502, detail="The chat service is unavailable.") from None

    if not upstream.ok:
        # Avoid forwarding upstream bodies or headers, which may contain sensitive details.
        logger.warning("Ollama Cloud returned HTTP %s", upstream.status_code)
        raise HTTPException(status_code=502, detail="The chat service returned an error.")

    try:
        result = upstream.json()
        response_text = result["message"]["content"]
        if not isinstance(response_text, str):
            raise TypeError("Unexpected response content type")
    except (ValueError, KeyError, TypeError):
        logger.warning("Ollama Cloud returned an invalid response")
        raise HTTPException(status_code=502, detail="The chat service returned an invalid response.") from None

    return ChatResponse(response=response_text)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
