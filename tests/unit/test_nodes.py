"""单元测试 — 各节点独立功能测试。"""
import pytest

from app.core.agent.nodes.chat_node import chat_node
from app.core.agent.nodes.generator import generator_node
from app.core.agent.state import AgentState


def test_chat_node_returns_messages():
    """chat_node 应该返回 messages 字段。"""
    state: AgentState = {"messages": [("human", "你好")]}
    result = chat_node(state)
    assert "messages" in result
    assert len(result["messages"]) == 1


def test_generator_node_without_docs():
    """generator_node 如果没有检索文档，应该仍然能回复。"""
    state: AgentState = {
        "messages": [("human", "你好")],
        "retrieved_docs": [],
        "intent": "qa",
        "sub_questions": [],
        "reranked_docs": [],
        "generation_attempts": 0,
    }
    result = generator_node(state)
    assert "messages" in result
