"""
文档导入管线 — 将原始文档导入向量库

学习点：
1. Document Loader：读取不同格式的文档，统一为 Document 对象
2. Text Splitter：将长文档切分成小片段（chunk）
3. Embedding：将文本片段转为向量
4. Vector Store：存储向量 + 元数据

Pipeline 流程：
    原始文件 → Loader → Documents → Splitter → Chunks → Embedding → Vector Store

关键参数（chunk_size / chunk_overlap）：
    - chunk_size=500：每个片段约 500 个字符（中文约 200-300 字）
    - chunk_overlap=50：片段间重叠 50 字符，防止上下文断裂
"""
import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.retrieval.vector_store import get_vector_store


def load_documents(docs_dir: str | Path) -> List[Document]:
    """
    从目录加载所有文本文档。

    支持 .txt / .md / .py 等纯文本格式。
    PDF/Word 支持需要在 Phase 5 之后添加（需要装 unstructured/pdfplumber）。
    """
    docs_dir = Path(docs_dir)
    if not docs_dir.exists():
        raise FileNotFoundError(f"文档目录不存在: {docs_dir}")

    loader = DirectoryLoader(
        str(docs_dir),
        glob="**/*.txt",       # 加载所有 .txt 文件
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    docs = loader.load()
    print(f"  加载了 {len(docs)} 个文件")
    return docs


def split_documents(docs: List[Document]) -> List[Document]:
    """
    将文档切分成小片段。

    RecursiveCharacterTextSplitter 是 LangChain 推荐的通用分块器。
    它的策略：
        1. 优先按段落 (\n\n) 切
        2. 段落太长再按句子 (。！？) 切
        3. 句子太长再按逗号切
        4. 最后按字符数硬切

    这样能最大程度保留语义完整性。
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,          # 每个片段大小（字符数）
        chunk_overlap=50,        # 片段间重叠（防止从中间截断）
        separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(docs)
    print(f"  切分成 {len(chunks)} 个片段")
    return chunks


def ingest_directory(docs_dir: str | Path):
    """
    完整的导入流程：加载 → 分块 → 向量化 → 入库

    用法:
        ingest_directory("data/knowledge/")
    """
    print(f"\n{'='*50}")
    print(f"开始导入文档: {docs_dir}")

    # 1. 加载
    print("步骤 1/3: 加载文档...")
    docs = load_documents(docs_dir)

    if not docs:
        print("  没有找到文档，跳过导入")
        return

    # 2. 分块
    print("步骤 2/3: 切分文档...")
    chunks = split_documents(docs)

    # 3. 入库
    print("步骤 3/3: 向量化并存入 Chroma...")
    store = get_vector_store()
    store.add_documents(chunks)
    # Chroma 会自动持久化到磁盘

    print(f"\n✅ 导入完成！{len(chunks)} 个片段已入库")
    print(f"   向量库位置: {settings.vector_store_path}")
