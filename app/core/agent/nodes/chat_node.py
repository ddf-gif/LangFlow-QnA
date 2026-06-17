"""
对话节点 — 调用 LLM 生成回复

这是整个 Agent 中最基础的节点。
Phase 1 中，它是唯一的节点。后续 Phase 中，它负责"闲聊"场景。

学习点：
1. 节点函数接收 state，返回 dict（要更新的字段）
2. messages 的 add_messages 行为——自动追加回复
3. 节点不应该修改 state 本身，而是返回要更新的内容

深入理解：
    LangGraph 的 Node 本质上是一个 reducer。
    它接收当前状态，返回"要做的修改"。
    Graph 框架负责将这些修改应用到状态上。
"""

from typing import Any, Dict

from app.core.agent.state import AgentState
from app.core.llm.factory import create_llm


def chat_node(state: AgentState) -> Dict[str, Any]:
    """
    对话节点：调用 LLM 回复用户。

    Args:
        state: 当前的 AgentState（包含历史消息列表）

    Returns:
        dict: 更新到 AgentState 的字段
              {"messages": [AIMessage(...)]}
              add_messages 会自动将它追加到消息列表末尾
    """

    # 1. 创建 LLM 实例
    llm = create_llm()
    # Phase 1 不传任何系统提示词，后续可以加：
    # llm = create_llm().bind(system_prompt="你是一个知识库助手")

    # 2. 调用 LLM
    #    state["messages"] 包含了整个对话历史
    #    第一次调用时: [HumanMessage(content="你好")]
    #    第二次调用时: [HumanMessage(...), AIMessage(...), HumanMessage(...)]
    response = llm.invoke(state["messages"])

    # 3. 返回要追加的消息
    #    注意：不需要手动修改 state["messages"]
    #    add_messages reducer 会自动将返回的消息追加到列表中
    return {"messages": [response]}
