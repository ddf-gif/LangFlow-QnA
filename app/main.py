"""
FastAPI 应用入口。

启动:
    uvicorn app.main:app --reload
访问:
    http://127.0.0.1:8000  — 前端聊天界面
    http://127.0.0.1:8000/docs  — API 文档
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router

app = FastAPI(
    title="LangFlow-QnA",
    description="基于 LangChain + LangGraph 的知识库智能问答 Agent 系统",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由（必须在静态文件挂载之前）
app.include_router(chat_router)
app.include_router(documents_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


# 前端页面
static_dir = Path(__file__).parent / "static"
index_html = static_dir / "index.html"


@app.get("/")
async def serve_frontend():
    if index_html.exists():
        return FileResponse(str(index_html))
    return {"message": "Frontend not built yet"}


# 静态资源（CSS/JS 等）
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
