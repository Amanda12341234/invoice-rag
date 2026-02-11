from typing import Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_history: list[ChatMessage] = []


class ChatSource(BaseModel):
    invoice_id: Optional[int] = None
    store_name: Optional[str] = None
    date: Optional[str] = None
    relevance: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource] = []
