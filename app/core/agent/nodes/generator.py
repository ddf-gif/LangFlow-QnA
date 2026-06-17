"""
生成节点 — 基于检索结果 + 对话历史生成回答

这就是 RAG 的"AG"（Augmented Generation）：
    将检索到的文档作为"参考资料"注入到 LLM 的上下文中。

学习点：
1. Augmented（增强）的含义：给 LLM 提供它本身不知道的信息
2. Prompt 设计的关键：明确告诉 LLM "只基于提供的资料回答"
3. 如果资料不够 → 让 LLM 说"不知道" → 避免幻觉
"""
from typing import Any, Dict

from app.core.agent.state import AgentState
from app.core.llm.factory import create_llm


# ──────────────────────────────────────────────
# 系统提示词：告诉 LLM 如何基于知识库回答
# ──────────────────────────────────────────────
# 为什么这么写：
#   - 明确"知识库内容"和"对话历史"是两个来源
#   - 强调"如果知识库没有相关信息，说不知道"
#   - 防止 LLM 用自己的知识回答（避免幻觉）
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """你是一个知识库问答助手。

请基于以下知识库内容来回答用户的问题。
如果知识库内容不足以回答，请直接说"我没有找到相关信息"。

知识库内容：
{context}

对话历史：
{history}

用户问题：{question}

回答要求：
1. 只基于知识库内容回答
2. 如果知识库没有相关信息，明确说"我没有找到相关信息"
3. 用中文回答，语言简洁准确"""


def generator_node(state: AgentState) -> Dict[str, Any]:
    """
    生成节点：基于检索到的文档生成回答。

    这个节点做了三件事：
    1. 把检索到的文档拼接成上下文
    2. 组装 System Prompt（知识库内容 + 对话历史 + 问题）
    3. 调用 LLM 生成回答
    """

    # 1. 提取用户问题
    last_message = state["messages"][-1]
    question = last_message.content

    # 2. 拼接检索到的文档内容
    #    每个 Document 有 page_content 和 metadata 两个属性
    context_parts = []
    for i, doc in enumerate(state.get("retrieved_docs", []), 1):
        source = doc.metadata.get("source", "未知来源")
        context_parts.append(f"[{i}] 来自 {source}:\n{doc.page_content}")
    context = "\n\n".join(context_parts)

    # 3. 拼接对话历史（最近 3 轮）
    #    -1 是当前问题，所以取 [-3:-1] 作为历史
    history_messages = state["messages"][-5:-1]  # 取最近几条历史
    history_text = "\n".join(
        f"{'用户' if m.type == 'human' else '助手'}: {m.content}"
        for m in history_messages
    )

    # 4. 组装 final prompt
    prompt = SYSTEM_PROMPT.format(
        context=context or "（暂无知识库内容）",
        history=history_text or "（无）",
        question=question,
    )

    # 5. 调用 LLM
    llm = create_llm(temperature=0.3)  # RAG 场景用低温度，更准确
    response = llm.invoke([
        ("system", prompt),
        ("human", question),
    ])

    return {"messages": [response]}
