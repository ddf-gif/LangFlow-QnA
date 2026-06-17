"""
兜底节点 — 当检索无结果或意图无法识别时的保底处理

学习点：
- 一个完善的 Agent 必须有 fallback 机制
- 不要让 LLM 在无信息时自己编造答案
"""
from typing import Any, Dict

from app.core.llm.factory import create_llm


def fallback_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """兜底处理：礼貌告知用户无法回答。"""
    llm = create_llm(temperature=0.5)
    response = llm.invoke([
        (
            "system",
            "你是LangFlow问答助手。如果用户的问题你无法回答或不在你知识范围内，"
            "请礼貌地告诉用户，并引导用户提出其他问题。保持友好和 helpful。",
        ),
        *state["messages"][-3:],
    ])
    return {"messages": [response]}
