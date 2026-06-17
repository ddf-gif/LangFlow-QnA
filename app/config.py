"""
配置管理 — 通过环境变量加载配置

学习点：
- pydantic-settings 自动从 .env 文件加载配置
- 所有敏感信息（API Key）通过环境变量注入，不硬编码
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM 配置
    llm_api_key: str = "sk-placeholder"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # 向量库
    vector_store_path: str = "./data/vector_store"
    vector_store_collection: str = "knowledge_base"

    # 检索参数
    retrieval_top_k: int = 5
    retrieval_score_threshold: float = 0.3

    # 应用
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
