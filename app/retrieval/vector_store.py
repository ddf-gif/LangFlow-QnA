"""
向量存储封装 — Chroma

学习点：
- LangChain 的 VectorStore 抽象层：统一接口，可换后端
- Chroma：本地运行，无需 Docker，适合学习和原型
- 依赖注入：vectore_store 作为单例，各节点共享

LangChain 向量存储的核心方法：
    .add_documents(docs)       → 存入文档
    .similarity_search(query)  → 返回相似文档
    .similarity_search_with_relevance_scores(query) → 带分数
"""
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings


# ──────────────────────────────────────────────
# Embedding 模型：将文本转为向量
# ──────────────────────────────────────────────
# 为什么用 HuggingFace 本地模型？
#   - 零成本（无 API 调用费）
#   - BAAI/bge-small-zh-v1.5 对中文效果好，模型仅 30MB
#   - 可离线运行
# 如果后续想换成 API 版（如 text-embedding-3-small）：
#   from langchain_openai import OpenAIEmbeddings
#   embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
# ──────────────────────────────────────────────
def create_embeddings():
    """
    创建 Embedding 模型。

    使用 HuggingFace 本地模型，零成本、可离线。

    注意：
    - 在国内如果下载失败，设置环境变量 HF_ENDPOINT 使用镜像：
        set HF_ENDPOINT=https://hf-mirror.com    (Windows CMD)
        export HF_ENDPOINT=https://hf-mirror.com  (Linux/Mac)
    - 或者预先下载模型放到本地路径
    """
    import os
    # 如果设置了 HF_ENDPOINT 镜像，优先使用
    if "HF_ENDPOINT" not in os.environ:
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-zh-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


_embeddings_instance = None


def get_embeddings():
    """懒加载 Embedding 模型（首次调用时才下载）。"""
    global _embeddings_instance
    if _embeddings_instance is None:
        import os
        if "HF_ENDPOINT" not in os.environ:
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        _embeddings_instance = create_embeddings()
    return _embeddings_instance


def get_vector_store() -> Chroma:
    """
    获取（或创建）向量存储实例。

    持久化路径由 settings.vector_store_path 控制，
    默认保存在 ./data/vector_store/

    注意：embeddings 是懒加载的，首次调用 get_vector_store()
    或 get_retriever() 时才会下载模型。
    """
    return Chroma(
        collection_name=settings.vector_store_collection,
        embedding_function=get_embeddings(),
        persist_directory=str(settings.vector_store_path),
    )


def get_retriever(k: int | None = None) -> VectorStoreRetriever:
    """
    获取检索器（VectorStoreRetriever 封装了 search + filter）

    用法:
        retriever = get_retriever(k=5)
        docs = retriever.invoke("公司2024年营收")
    """
    vs = get_vector_store()
    return vs.as_retriever(
        search_kwargs={"k": k or settings.retrieval_top_k}
    )
