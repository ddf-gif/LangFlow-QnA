"""
调试脚本 — 看 RAG 全流程：检索了什么 + 最终答案
"""
import sys
sys.path.insert(0, ".")

from app.core.agent.graph import agent_graph

config = {"configurable": {"thread_id": "debug-1"}}

# 执行一次问答
result = agent_graph.invoke(
    {"messages": [("human", "LangFlow 2024年营收多少")]},
    config=config,
)

print("===== 🗂️ 检索到的文档片段 =====")
for i, doc in enumerate(result.get("retrieved_docs", []), 1):
    print(f"\n--- 片段 {i} ---")
    print(doc.page_content[:200] + "...")
    print(f"(来源: {doc.metadata.get('source', '未知')})")

print("\n\n===== 🤖 最终答案 =====")
print(result["messages"][-1].content)
