"""API 请求/响应模型。"""
from typing import List, Optional

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


class DocItem(BaseModel):
    """文档清单条目。"""
    id: str
    filename: str
    source: str
    ext: str
    size: int
    chunks: int
    category: str
    uploaded_at: str


class DocListResponse(BaseModel):
    """文档列表响应。"""
    total: int
    items: List[DocItem]


class ChunkPreview(BaseModel):
    """单个片段预览。"""
    index: int
    text: str


class DocDetailResponse(BaseModel):
    """文档详情响应（含片段预览）。"""
    id: str
    filename: str
    source: str
    ext: str
    size: int
    chunks: int
    category: str
    uploaded_at: str
    content: str
    chunk_previews: List[ChunkPreview]


class CategoryStat(BaseModel):
    """分类统计。"""
    name: str
    count: int
    chunks: int


class RecentQa(BaseModel):
    """最近问答记录。"""
    question: str
    answer: str
    status: str
    time: str
    latency: str


class StatsResponse(BaseModel):
    """数据看板统计响应。"""
    kb_count: int
    doc_count: int
    total_chunks: int
    qa_count: int
    retrieval_success_rate: float
    categories: List[CategoryStat]
    recent_qa: List[RecentQa]


class UploadResponse(BaseModel):
    """上传响应。"""
    filename: str
    chunks: int
    category: str
    size: int
    message: str


class RoleItem(BaseModel):
    """角色条目。"""
    id: str
    name: str
    group: str
    permissions: str
    creator: str
    created_at: str


class RoleListResponse(BaseModel):
    """角色列表响应。"""
    total: int
    items: List[RoleItem]


class CreateRoleRequest(BaseModel):
    """创建角色请求。"""
    name: str
    group: str = "编辑者"
    permissions: str = ""
    creator: str = "当前用户"

