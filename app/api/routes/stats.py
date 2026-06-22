"""数据看板统计 API。"""
from datetime import datetime
from typing import List

from fastapi import APIRouter

from app.api.schemas import StatsResponse, CategoryStat, RecentQa
from app.services import doc_registry
from app.services.session import session_manager

router = APIRouter(prefix="/api/stats", tags=["stats"])

# 内存级最近问答记录（由 chat 路由上报）
# 生产环境应持久化到数据库；当前用于看板展示。
_recent_qa: List[dict] = []
_MAX_RECENT = 20


def record_qa(question: str, answer: str, latency_ms: float, success: bool) -> None:
    """记录一次问答，供数据看板展示。"""
    _recent_qa.insert(0, {
        "question": question,
        "answer": answer,
        "status": "成功" if success else "失败",
        "time": datetime.now().strftime("%H:%M"),
        "latency": f"{latency_ms / 1000:.1f}s",
    })
    del _recent_qa[_MAX_RECENT:]


@router.get("", response_model=StatsResponse)
async def get_stats():
    """聚合知识库 / 文档 / 片段 / 问答统计数据。"""
    docs = doc_registry.list_docs()
    categories = doc_registry.get_categories()

    doc_count = len(docs)
    total_chunks = sum(d.get("chunks", 0) for d in docs)
    kb_count = len([c for c in categories if c["count"] > 0])

    # 问答总量：所有会话的消息计数之和 + 最近记录
    qa_count = session_manager.total_count() if hasattr(session_manager, "total_count") else len(_recent_qa)

    # 检索成功率：基于最近问答的成功比例
    if _recent_qa:
        ok = sum(1 for q in _recent_qa if q["status"] == "成功")
        success_rate = round(ok / len(_recent_qa) * 100, 1)
    else:
        success_rate = 100.0

    cat_stats = [CategoryStat(**c) for c in categories]
    recent = [RecentQa(**q) for q in _recent_qa[:5]]

    return StatsResponse(
        kb_count=kb_count,
        doc_count=doc_count,
        total_chunks=total_chunks,
        qa_count=qa_count,
        retrieval_success_rate=success_rate,
        categories=cat_stats,
        recent_qa=recent,
    )
