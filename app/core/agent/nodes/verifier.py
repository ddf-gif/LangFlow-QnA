"""
验证节点 — 检查回答是否基于检索文档生成，防止幻觉

这是 RAG 质量保障的最后一道关卡。
它检查：
1. 回答中的关键信息是否能在检索文档中找到依据
2. 如果找不到依据 → 标记为"幻觉" → 触发重新检索+生成

学习点：
- "LLM as Judge" 模式：用 LLM 来评判 LLM 的输出
- 验证节点返回分支决策 → 条件边决定下一步走哪条路
- retry 机制：验证不通过则重新检索（最多重试 2 次）
"""
from typing import Any, Dict

from app.core.llm.factory import create_llm

VERIFY_PROMPT = """检查以下回答是否基于提供的知识库内容。

知识库内容：
{context}

回答：
{answer}

检查标准：
1. 回答中的关键数字、事实是否能在知识库中找到？
2. 回答是否包含了知识库中没有的信息？
3. 如果知识库没有相关信息，回答是否明确说"不知道"？

只返回 JSON 格式：
{{"pass": true/false, "reason": "简要说明"}}"""


def verifier_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证节点：检查生成质量，决定继续还是重新检索。

    返回条件路由所需的标记：
    - "pass": 验证通过
    - "retry": 需要重新检索+生成
    - "max_retries": 已达最大重试次数，直接结束
    """
    # 防止无限循环：最多重试 2 次
    attempts = state.get("generation_attempts", 0)
    if attempts >= 2:
        return {"generation_attempts": attempts + 1}

    answer = state["messages"][-1].content
    docs = state.get("reranked_docs") or state.get("retrieved_docs", [])
    context = "\n\n".join(d.page_content[:500] for d in docs[:3]) if docs else ""

    if not context:
        # 没有检索到文档，直接通过让 fallback 处理
        return {"generation_attempts": attempts + 1}

    prompt = VERIFY_PROMPT.format(context=context, answer=answer)

    llm = create_llm(temperature=0)
    response = llm.invoke(prompt)

    try:
        import json
        result = json.loads(response.content)
        is_pass = result.get("pass", False)
    except (json.JSONDecodeError, KeyError, TypeError):
        is_pass = True  # 解析失败默认通过

    if is_pass:
        return {"generation_attempts": 0}  # 重置计数器
    else:
        return {"generation_attempts": attempts + 1}
