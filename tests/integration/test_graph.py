"""集成测试 — LangGraph 工作流端到端测试。"""
import pytest

from app.core.agent.graph import build_graph


@pytest.fixture
def graph():
    return build_graph()


def test_graph_compiles(graph):
    """图应该能成功编译。"""
    assert graph is not None


def test_graph_has_all_nodes(graph):
    """图应该包含所有预期的节点。"""
    expected = {
        "intent_router", "retriever", "reranker",
        "generator", "verifier", "chat", "fallback",
    }
    assert expected.issubset(set(graph.nodes))


def test_graph_qa_flow(graph):
    """QA 流程应该能正常运行。"""
    result = graph.invoke(
        {"messages": [("human", "LangFlow 2024年营收多少")]},
        config={"configurable": {"thread_id": "integ-test-qa"}},
    )
    assert "messages" in result
    assert result["messages"][-1].type == "ai"


def test_graph_chat_flow(graph):
    """闲聊流程应该不走检索。"""
    result = graph.invoke(
        {"messages": [("human", "你好")]},
        config={"configurable": {"thread_id": "integ-test-chat"}},
    )
    assert "messages" in result
    assert result["messages"][-1].type == "ai"


def test_graph_preserves_history(graph):
    """同一个 thread_id 应该保留对话历史。"""
    thread = "integ-test-history"
    graph.invoke(
        {"messages": [("human", "我的名字是张三")]},
        config={"configurable": {"thread_id": thread}},
    )
    result = graph.invoke(
        {"messages": [("human", "我叫什么名字")]},
        config={"configurable": {"thread_id": thread}},
    )
    reply = result["messages"][-1].content
    assert "张三" in reply
