"""
Agent 节点（Node）注册中心

每个节点是一个独立的函数，负责 Agent 工作流中的一个处理步骤。
节点通过 AgentState 通信，不直接调用对方。
"""
from app.core.agent.nodes.chat_node import chat_node
from app.core.agent.nodes.retriever import retriever_node
from app.core.agent.nodes.generator import generator_node
from app.core.agent.nodes.intent_router import intent_router
from app.core.agent.nodes.fallback import fallback_node
from app.core.agent.nodes.reranker import reranker_node
from app.core.agent.nodes.verifier import verifier_node

__all__ = [
    "chat_node",
    "retriever_node",
    "generator_node",
    "intent_router",
    "fallback_node",
    "reranker_node",
    "verifier_node",
]
