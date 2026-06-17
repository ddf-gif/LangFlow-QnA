"""
FastAPI 应用入口。

启动:
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router

app = FastAPI(
    title="LangFlow-QnA",
    description="基于 LangChain + LangGraph 的知识库智能问答 Agent 系统",
    version="0.1.0",
)

# CORS 配置（允许前端跨域调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
