"""
测试：Phase 1 — LangGraph 图能正确编译

这是最基本的测试——验证我们的工作流图能编译成功。
在运行任何对话之前，先确保图结构是正确的。

学习点：
- pytest 的基本用法
- LangGraph 图的编译验证
- 测试先行（先写测试，再实现）
"""
from app.core.agent.graph import build_graph


def test_graph_compiles():
    """图应该能成功编译，不抛出异常"""
    graph = build_graph()
    assert graph is not None


def test_graph_has_correct_nodes():
    """图应该包含预期的节点"""
    graph = build_graph()
    nodes = graph.nodes
    # Phase 1 只有一个 chat 节点
    assert "chat" in nodes


def test_graph_can_invoke():
    """图应该能接收输入并返回输出（集成测试）"""
    graph = build_graph()
    result = graph.invoke(
        {"messages": [("human", "你好，请回复一句问候")]},
        config={"configurable": {"thread_id": "test-1"}},
    )
    assert "messages" in result
    assert len(result["messages"]) > 0
    # 最后一条消息应该是 AI 的回复
    assert result["messages"][-1].type == "ai"
    # 回复不应该为空
    assert result["messages"][-1].content.strip() != ""
