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
from app.api.routes.stats import router as stats_router
from app.api.routes.categories import router as categories_router
from app.api.routes.roles import router as roles_router
from app.api.routes.auth import router as auth_router
from app.services import doc_registry

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
app.include_router(stats_router)
app.include_router(categories_router)
app.include_router(roles_router)
app.include_router(auth_router)


@app.on_event("startup")
async def _startup_migrate():
    """启动时确保文档注册表已初始化（首次会从向量库迁移）。"""
    try:
        doc_registry.migrate_from_vector_store()
    except Exception as e:  # 迁移失败不应阻断启动
        print(f"[startup] 文档注册表迁移失败: {e}")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/favicon.ico")
async def favicon():
    """返回内嵌的 favicon，避免浏览器控制台 404。"""
    from fastapi.responses import Response
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><text y="28" font-size="28">🧠</text></svg>'
    return Response(content=svg, media_type="image/svg+xml")


# 前端页面
static_dir = Path(__file__).parent / "static"
admin_dir = static_dir / "admin"
index_html = static_dir / "index.html"
admin_index = admin_dir / "index.html"
login_html = static_dir / "login.html"


@app.get("/login")
async def serve_login():
    """登录页面。"""
    if login_html.exists():
        return FileResponse(str(login_html))
    return {"message": "Login page not available"}


@app.get("/")
async def serve_frontend():
    """C 端用户问答界面。"""
    if index_html.exists():
        return FileResponse(str(index_html))
    return {"message": "Frontend not built yet"}


@app.get("/admin/")
async def serve_admin():
    """B 端管理后台。"""
    if admin_index.exists():
        return FileResponse(str(admin_index))
    return {"message": "Admin panel not available"}


# 静态资源（CSS/JS 等）
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
