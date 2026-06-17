"""
意图识别节点 — 判断用户问题的类型，决定走哪条处理分支

为什么要做意图识别？
    不是所有问题都需要检索知识库：
    - "你好" → 闲聊，直接回复（更快、省 Token）
    - "2024年营收多少" → QA 问答，需要检索
    - "帮我把刚才的内容总结一下" → 需要总结
"""
from typing import Any, Dict

from app.core.llm.factory import create_llm

INTENT_PROMPT = """判断用户最近一条消息的意图，只返回一个词。

分类：
- qa: 需要从知识库检索信息来回答的问题（事实性、数据性查询）
- chat: 问候、闲聊、无需检索的日常对话
- summarize: 要求总结或概括已有内容
- fallback: 无法判断或其他情况

用户消息：{message}
对话历史（最近3轮）：{history}

只输出分类名称（qa/chat/summarize/fallback）："""


def intent_router(state: Dict[str, Any]) -> Dict[str, Any]:
    """判断用户意图并路由到对应处理分支。"""
    last_msg = state["messages"][-1]
    question = last_msg.content

    # 拼接最近对话历史
    history_msgs = state["messages"][-5:-1]
    history = "\n".join(
        f"{'用户' if m.type == 'human' else '助手'}: {m.content}"
        for m in history_msgs
    )

    prompt = INTENT_PROMPT.format(message=question, history=history or "无")

    llm = create_llm(temperature=0)
    response = llm.invoke(prompt)
    intent = response.content.strip().lower()

    # 兜底
    if intent not in ("qa", "chat", "summarize", "fallback"):
        intent = "fallback"

    return {"intent": intent}
