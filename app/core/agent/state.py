"""
Agent 状态定义 — 最终版本 (Phase 1-4)

字段增长规律:
    Phase 1: messages                           # 纯对话
    Phase 2: + retrieved_docs                   # RAG
    Phase 3: + intent, sub_questions            # 意图路由
    Phase 4: + reranked_docs, generation_attempts # 质量增强
"""
from typing import Annotated, List, TypedDict

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Agent 的全局状态。"""

    # Phase 1: 对话历史（自动追加）
    messages: Annotated[List[AnyMessage], add_messages]

    # Phase 2: 检索结果
    retrieved_docs: List[Document]

    # Phase 3: 意图路由
    intent: str                # "qa" | "chat" | "summarize" | "fallback"
    sub_questions: List[str]   # 复杂问题拆解后的子问题列表

    # Phase 4: 质量增强
    reranked_docs: List[Document]      # 重排序后的文档
    generation_attempts: int           # 生成重试次数（防无限循环）
