"""
检索节点 — 多路召回 + 句子窗口扩展

学习点：
1. 多路召回（Multi-Query Retrieval）：
   - 路线①：原始查询直接向量检索
   - 路线②：HyDE — 先让 LLM 写一个"假设性回答"，用它去检索（更适合语义模糊的问题）
   - 路线③：查询扩展 — 让 LLM 改写出同义问句，分别检索
   - 三路结果去重合并，提升召回率
2. 句子窗口（Sentence Window）：
   - 检索命中的 chunk 只有一小段文本，可能丢失上下文
   - 命中 chunk 后，再从向量库中取出它的"前后邻居"（同 source、chunk_index 相邻）
   - 拼接成更完整的上下文窗口

执行流程:
    用户问题
        ├──→ ① 向量检索（原始查询）
        ├──→ ② HyDE（LLM 假设回答 → 检索）
        └──→ ③ 查询扩展（LLM 改写 → 多次检索）
              ↓ 去重合并
         句子窗口扩展（合并相邻 chunk）
              ↓
         {"retrieved_docs": [...]}
"""
from typing import Any, Dict, List

from langchain_core.documents import Document

from app.core.agent.state import AgentState
from app.retrieval.vector_store import get_retriever, get_vector_store


# A/B 评估开关：True = 旧版单路检索，False = 多路召回+句子窗口
BASELINE_MODE = False


# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────

def _dedup(docs: List[Document]) -> List[Document]:
    """按 (source, page_content 前缀) 去重。"""
    seen = set()
    result = []
    for d in docs:
        key = (d.metadata.get("source", ""), d.page_content[:80])
        if key not in seen:
            seen.add(key)
            result.append(d)
    return result


def _truncate(docs: List[Document], limit: int = 8) -> List[Document]:
    """截断到最多 limit 个片段。"""
    return docs[:limit]


# ──────────────────────────────────────────────
# 三路召回策略
# ──────────────────────────────────────────────

def _route_vector(query: str, k: int = 5) -> List[Document]:
    """路线①：原始查询直接向量检索。"""
    return get_retriever(k=k).invoke(query)


def _route_hyde(query: str, k: int = 5) -> List[Document]:
    """路线②：HyDE — 让 LLM 先写一个假设性回答，用它去检索。

    原理：用户的问题往往简短，而知识库里的内容是陈述句。
    让 LLM 先"脑补"一个可能的答案，这个答案在向量空间里更接近真正的文档。
    """
    try:
        from app.core.llm.factory import create_llm
        llm = create_llm(temperature=0.0)
        prompt = (
            "请根据以下问题，写一段 200 字以内的、可能出现在知识库中的回答段落。"
            "只输出回答内容，不要解释。\n\n问题：" + query
        )
        hypo = llm.invoke(prompt).content.strip()
        if not hypo:
            return []
        return get_retriever(k=k).invoke(hypo)
    except Exception:
        return []


def _route_query_expansion(query: str, k: int = 3) -> List[Document]:
    """路线③：查询扩展 — 让 LLM 生成 2 个同义改写，分别检索。

    原理：同一个意思可以用不同表达。LLM 改写后可能命中原始查询漏掉的文档。
    """
    try:
        from app.core.llm.factory import create_llm
        llm = create_llm(temperature=0.3)
        prompt = (
            "请把下面的问题改写成 2 个意思相同但表达不同的问句，每行一个，不加序号。\n\n"
            "原问题：" + query
        )
        raw = llm.invoke(prompt).content.strip()
        lines = [ln.strip() for ln in raw.split("\n") if ln.strip()][:2]
        results = []
        for q in lines:
            if q and q != query:
                results.extend(get_retriever(k=k).invoke(q))
        return results
    except Exception:
        return []


# ──────────────────────────────────────────────
# 句子窗口扩展
# ──────────────────────────────────────────────

def _expand_sentence_window(docs: List[Document], window: int = 1) -> List[Document]:
    """句子窗口扩展：对每个命中的 chunk，把它同 source 的前后相邻 chunk 也拉出来。

    依赖 chunk 元数据中的 chunk_index 字段（由 pipeline.py 写入）。
    window=1 表示取前后各 1 个相邻片段。

    实现方式：用 Chroma 的 where 过滤 + 原文拼接。
    为避免过度膨胀，只对前 N 个命中片段做窗口扩展。
    """
    if not docs:
        return docs

    try:
        vs = get_vector_store()
    except Exception:
        return docs

    expanded: List[Document] = []
    for doc in docs[:5]:  # 只对前 5 个命中片段做窗口扩展
        source = doc.metadata.get("source")
        idx = doc.metadata.get("chunk_index")
        if source is None or idx is None:
            expanded.append(doc)
            continue

        # 查询相邻 chunk（同 source、chunk_index 在 ±window 范围）
        neighbor_indices = list(range(idx - window, idx + window + 1))
        try:
            res = vs.get(
                where={
                    "$and": [
                        {"source": source},
                        {"chunk_index": {"$in": neighbor_indices}},
                    ]
                },
                include=["documents", "metadatas"],
            )
            neighbor_docs = []
            for text, meta in zip(
                res.get("documents", []) or [],
                res.get("metadatas", []) or [],
            ):
                neighbor_docs.append(Document(page_content=text, metadata=meta or {}))
            # 按 chunk_index 排序，保证阅读顺序
            neighbor_docs.sort(key=lambda d: d.metadata.get("chunk_index", 0))

            if neighbor_docs:
                # 把相邻片段拼成一个更大的上下文块
                merged_text = "\n".join(d.page_content for d in neighbor_docs)
                expanded.append(Document(
                    page_content=merged_text,
                    metadata={**doc.metadata, "window_expanded": True},
                ))
            else:
                expanded.append(doc)
        except Exception:
            expanded.append(doc)

    return expanded


# ──────────────────────────────────────────────
# 主节点函数
# ──────────────────────────────────────────────

def retriever_node(state: AgentState) -> Dict[str, Any]:
    """
    检索节点：多路召回 + 句子窗口扩展。

    流程：
        1. 三路并行召回（向量 + HyDE + 查询扩展）
        2. 去重合并
        3. 句子窗口扩展（拼接相邻 chunk）
        4. 截断到合理数量
    """
    last_message = state["messages"][-1]
    query = last_message.content

    # A/B 评估：BASELINE_MODE=True 时退化为单路向量检索
    if BASELINE_MODE:
        docs = get_retriever(k=5).invoke(query)
        print(f"  [retriever] 基线模式: 单路向量检索 → {len(docs)} 个结果")
        return {"retrieved_docs": docs}

    # 1. 三路召回
    docs_vector = _route_vector(query, k=5)
    docs_hyde = _route_hyde(query, k=4)
    docs_expand = _route_query_expansion(query, k=3)

    # 2. 去重合并
    merged = _dedup(docs_vector + docs_hyde + docs_expand)

    # 3. 句子窗口扩展
    expanded = _expand_sentence_window(merged, window=1)

    # 4. 截断
    final = _truncate(expanded, limit=8)

    print(f"  [retriever] 多路召回: 向量={len(docs_vector)} HyDE={len(docs_hyde)} 扩展={len(docs_expand)} → 合并去重={len(merged)} → 窗口扩展后={len(final)}")
    return {"retrieved_docs": final}
