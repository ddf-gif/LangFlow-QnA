"""
重排序节点 — 对检索结果进行精排，提升 Top-K 质量

为什么需要重排序？
    向量检索的 top-K 结果中，只有前 1-2 条通常是最相关的。
    重排序用更精确的模型对结果重新打分，把最相关的排到前面。

这里我们使用 LLM 打分作为重排序（不需要额外模型），
Phase 4 之后可以替换为专用的 Cross-Encoder 模型。
"""
import json
from typing import Any, Dict, List

from langchain_core.documents import Document

from app.core.llm.factory import create_llm


def _llm_rerank(query: str, docs: List[Document]) -> List[Document]:
    """
    用 LLM 对文档片段进行相关性打分重排序。

    给 LLM 每个片段和原始问题，让它打分（1-10），
    然后按分数降序排列。
    """
    if not docs:
        return []

    # 让 LLM 打分
    doc_texts = "\n\n".join(
        f"[{i}] {d.page_content[:300]}"
        for i, d in enumerate(docs)
    )
    prompt = f"""对以下文档片段与用户问题的相关性打分（1-10分），
只返回 JSON 格式的分数列表。

用户问题：{query}

文档片段：
{doc_texts}

返回格式：{{"scores": [分数1, 分数2, ...]}}
分数越高代表越相关。"""

    llm = create_llm(temperature=0)
    response = llm.invoke(prompt)

    try:
        scores = json.loads(response.content)["scores"]
    except (json.JSONDecodeError, KeyError, TypeError):
        # 解析失败则保持原顺序
        return docs

    # 按分数降序排列
    scored = list(zip(docs, scores))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scored]


def reranker_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    重排序节点：对检索到的文档重新排序。

    输入: state["retrieved_docs"]
    输出: state["reranked_docs"]
    """
    query = state["messages"][-1].content
    docs = state.get("retrieved_docs", [])

    if not docs:
        return {"reranked_docs": []}

    reranked = _llm_rerank(query, docs)
    return {"reranked_docs": reranked}
