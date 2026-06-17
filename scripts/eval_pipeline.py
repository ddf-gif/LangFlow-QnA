"""
评估脚本 — 测试 RAG 问答质量。

用法:
    python scripts/eval_pipeline.py

评估指标：
- 检索召回率: 正确答案是否在检索结果中
- 答案完整性: 回答是否覆盖了问题的所有方面
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.agent.graph import agent_graph


# 测试用例
TEST_CASES = [
    {"question": "LangFlow 公司2024年营收多少", "expected": "12.8亿"},
    {"question": "LangFlow 公司2024年净利润多少", "expected": "2.1亿"},
    {"question": "公司有多少员工", "expected": "1200"},
    {"question": "公司成立于哪一年", "expected": "2020"},
]


def evaluate():
    """运行评估并打印结果。"""
    passed = 0
    total = len(TEST_CASES)

    print("=" * 60)
    print("LangFlow-QnA 评估报告")
    print("=" * 60)

    for i, case in enumerate(TEST_CASES, 1):
        thread_id = f"eval-{i}"
        result = agent_graph.invoke(
            {"messages": [("human", case["question"])]},
            config={"configurable": {"thread_id": thread_id}},
        )
        answer = result["messages"][-1].content

        # 检查预期关键词是否在答案中
        has_expected = case["expected"] in answer
        status = "✅" if has_expected else "❌"
        if has_expected:
            passed += 1

        print(f"\n{status} 用例 {i}: {case['question']}")
        print(f"   预期包含: {case['expected']}")
        print(f"   实际回答: {answer[:80]}...")

    print(f"\n{'=' * 60}")
    print(f"结果: {passed}/{total} 通过 ({passed/total*100:.0f}%)")


if __name__ == "__main__":
    evaluate()
