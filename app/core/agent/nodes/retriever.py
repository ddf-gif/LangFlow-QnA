"""
检索节点 — 从向量库中检索相关文档

学习点：
1. 检索是 RAG 的"R"（Retrieval）— 决定 Agent 能看到什么信息
2. 检索结果的质量直接决定回答质量（Garbage In, Garbage Out）
3. 节点返回 {"retrieved_docs": [...]} 后，后续节点可以读取

执行流程:
    用户问题 → 向量化 → Chroma 相似度搜索 → 返回 top-k 文档

为什么用 .invoke 而不是 .similarity_search:
    VectorStoreRetriever 封装了 search + score_threshold + filter
    以后加过滤逻辑不用改节点代码
"""
from typing import Any, Dict

from app.core.agent.state import AgentState
from app.retrieval.vector_store import get_retriever


def retriever_node(state: AgentState) -> Dict[str, Any]:
    """
    检索节点：从向量库搜索与用户问题相关的文档片段。

    Args:
        state: 当前状态，包含 messages（从中取最后一条作为查询）

    Returns:
        dict: 更新 {"retrieved_docs": [Document, ...]}
    """

    # 1. 获取最后一条用户消息作为查询
    last_message = state["messages"][-1]
    query = last_message.content

    # 2. 检索
    retriever = get_retriever(k=5)
    docs = retriever.invoke(query)

    # 3. 返回检索结果
    #    注意：没有加 Annotated，所以会覆盖旧结果
    return {"retrieved_docs": docs}
