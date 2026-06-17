"""API 请求/响应模型。"""
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """对话请求。"""
    message: str
    session_id: str = "default"
    stream: bool = False


class ChatResponse(BaseModel):
    """对话响应。"""
    reply: str
    session_id: str
