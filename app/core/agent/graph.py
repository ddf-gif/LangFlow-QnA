"""
LangGraph 工作流定义 — 最终版本 (Phase 1-4)

工作流结构:
    entry → intent_router
      ├─ "qa" → retriever → reranker → generator → verifier
      │                                              ├─ "pass" → END
      │                                              ├─ "retry" → retriever ↻
      │                                              └─ "max_retries" → END
      ├─ "chat" → chat_node → END
      ├─ "summarize" → retriever → generator → END
      └─ "fallback" → fallback → END
"""
from typing import Any, Dict

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.core.agent.nodes import (
    chat_node,
    fallback_node,
    generator_node,
    intent_router,
    reranker_node,
    retriever_node,
    verifier_node,
)
from app.core.agent.state import AgentState


# ──────────────────────────────────────────────
# 条件路由函数
# ──────────────────────────────────────────────
def route_by_intent(state: Dict[str, Any]) -> str:
    """
    根据意图识别结果决定下一步走向。

    返回值 = 下一个节点的名称
    """
    intent = state.get("intent", "fallback")
    route_map = {
        "qa": "retriever",
        "summarize": "retriever",
        "chat": "chat",
        "fallback": "fallback",
    }
    return route_map.get(intent, "fallback")


def route_verification(state: Dict[str, Any]) -> str:
    """
    根据验证结果决定：通过、重试、或已达最大次数。

    读取 generation_attempts 字段：
    0 → 验证通过，结束
    1 → 验证不通过，重试检索
    2 → 已达最大重试次数，结束
    """
    attempts = state.get("generation_attempts", 0)
    if attempts == 0:
        return "pass"
    elif attempts <= 2:
        return "retry"
    else:
        return "max_retries"


# ──────────────────────────────────────────────
# 构建工作流图
# ──────────────────────────────────────────────
def build_graph() -> StateGraph:
    """构建完整的 Agent 工作流图。"""
    builder = StateGraph(AgentState)

    # ── 注册所有节点 ──
    builder.add_node("intent_router", intent_router)
    builder.add_node("retriever", retriever_node)
    builder.add_node("reranker", reranker_node)
    builder.add_node("generator", generator_node)
    builder.add_node("verifier", verifier_node)
    builder.add_node("chat", chat_node)
    builder.add_node("fallback", fallback_node)

    # ── 入口：从意图识别开始 ──
    builder.set_entry_point("intent_router")

    # ── 条件边：意图 → 路由 ──
    builder.add_conditional_edges(
        "intent_router",
        route_by_intent,
        {
            "retriever": "retriever",
            "chat": "chat",
            "fallback": "fallback",
        },
    )

    # ── QA 链路 ──
    builder.add_edge("retriever", "reranker")
    builder.add_edge("reranker", "generator")
    builder.add_edge("generator", "verifier")

    # ── 条件边：验证 → 通过/重试/放弃 ──
    builder.add_conditional_edges(
        "verifier",
        route_verification,
        {
            "pass": END,
            "retry": "retriever",      # 重新检索，走回 QA 链路
            "max_retries": END,        # 超限直接结束
        },
    )

    # ── 结束边 ──
    builder.add_edge("chat", END)
    builder.add_edge("fallback", END)

    graph = builder.compile(checkpointer=MemorySaver())
    return graph


# 全局可用的图实例
agent_graph = build_graph()


# ──────────────────────────────────────────────
# 命令行交互入口
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("LangFlow-QnA Agent — 完整版")
    print("输入 'exit' 退出")
    print("=" * 50)

    import uuid
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    while True:
        user_input = input("\n👤: ")
        if user_input.lower() in ("exit", "quit"):
            break

        result = agent_graph.invoke(
            {"messages": [("human", user_input)]},
            config=config,
        )
        print(f"\n🤖: {result['messages'][-1].content}")
