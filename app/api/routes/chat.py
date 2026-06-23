"""对话 API 路由。"""
import json
import time
from typing import AsyncGenerator

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.api.schemas import ChatRequest, ChatResponse
from app.core.agent.graph import agent_graph
from app.services.session import session_manager
from app.api.routes.stats import record_qa

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(req: ChatRequest) -> ChatResponse:
    """非流式对话接口。"""
    config = {"configurable": {"thread_id": req.session_id}}
    session_manager.get_or_create(req.session_id)
    session_manager.increment_count(req.session_id)
    start = time.time()
    success = True
    try:
        result = agent_graph.invoke(
            {"messages": [("human", req.message)]},
            config=config,
        )
        reply = result["messages"][-1].content
        # 提取检索来源
        sources = list(set(
            doc.metadata.get("source", "未知来源")
            for doc in result.get("retrieved_docs", [])
        ))
    except Exception:
        success = False
        reply = "抱歉，处理请求时出错，请稍后重试。"
        sources = []
    latency = (time.time() - start) * 1000
    record_qa(req.message, reply, latency, success)
    return ChatResponse(reply=reply, session_id=req.session_id, sources=sources)


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    """流式对话接口（SSE）。"""
    config = {"configurable": {"thread_id": req.session_id}}

    async def event_generator() -> AsyncGenerator:
        async for event in agent_graph.astream_events(
            {"messages": [("human", req.message)]},
            config=config,
            version="v2",
        ):
            kind = event.get("event", "")
            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk", "")
                if chunk:
                    yield {"event": "token", "data": json.dumps({"token": chunk})}

        yield {"event": "done", "data": json.dumps({"session_id": req.session_id})}

    return EventSourceResponse(event_generator())
