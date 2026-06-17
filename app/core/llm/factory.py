"""
LLM 工厂 — 创建和管理 LLM 实例

学习点：
- 使用 langchain-openai 的 ChatOpenAI 封装（兼容任何 OpenAI API 格式的提供商）
- 通过工厂模式统一管理 LLM 配置
- 可在未来扩展支持多种模型（如 DeepSeek、通义千问等）
"""
from langchain_openai import ChatOpenAI

from app.config import settings


def create_llm(**kwargs) -> ChatOpenAI:
    """
    创建一个 LLM 实例

    用法:
        llm = create_llm()                          # 使用默认配置
        llm = create_llm(model="gpt-4", temperature=0.0)  # 覆盖部分参数

    为什么用 ChatOpenAI:
        - DeepSeek、通义千问、Groq 等都兼容 OpenAI API 格式
        - 只需要换 base_url 和 api_key 就能切换模型
        - 这是 langchain 最成熟的 LLM 封装
    """
    return ChatOpenAI(
        api_key=kwargs.pop("api_key", settings.llm_api_key),
        base_url=kwargs.pop("base_url", settings.llm_base_url),
        model=kwargs.pop("model", settings.llm_model),
        temperature=kwargs.pop("temperature", settings.llm_temperature),
        max_tokens=kwargs.pop("max_tokens", settings.llm_max_tokens),
        **kwargs,
    )
