"""
调试脚本 — 只看检索这一步返回了什么
"""
import sys
sys.path.insert(0, ".")

from app.retrieval.vector_store import get_retriever

retriever = get_retriever(k=5)
docs = retriever.invoke("LangFlow 2024年营收多少")

print("===== 检索结果 =====")
print(f"共返回 {len(docs)} 个片段\n")

for i, doc in enumerate(docs):
    print(f"--- 片段 {i+1} ---")
    print(doc.page_content)
    print(f"(来源: {doc.metadata.get('source', '未知')})")
    print()
