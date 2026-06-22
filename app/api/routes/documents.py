"""文档管理 API — 上传 / 列表 / 详情 / 删除 / 重索引 / 批量分类。"""
import os
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from app.api.schemas import (
    DocItem,
    DocListResponse,
    DocDetailResponse,
    ChunkPreview,
    UploadResponse,
)
from app.ingestion.pipeline import ingest_file
from app.retrieval.vector_store import get_vector_store
from app.services import doc_registry

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 支持的文件扩展名（与 pipeline.load_single_file 一致）
SUPPORTED_EXTS = {".txt", ".md", ".py", ".js", ".ts", ".json", ".csv"}


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n} {unit}"
        n = n / 1024
    return f"{n} TB"


def _delete_chunks_by_source(source: str) -> int:
    """
    删除向量库中所有 source 匹配的 chunk。
    返回删除的片段数。
    """
    try:
        vs = get_vector_store()
        # 先按 source 过滤查出所有 chunk id，再删除
        res = vs.get(where={"source": source}, include=[])
        ids = res.get("ids", []) or []
        if ids:
            vs.delete(ids=ids)
        return len(ids)
    except Exception as e:
        print(f"[documents] 删除向量片段失败 (source={source}): {e}")
        return 0


# ─── 静态路径路由（必须在 {doc_id} 参数路由之前） ───

@router.get("", response_model=DocListResponse)
async def list_documents(
    category: Optional[str] = Query(None, description="按分类过滤"),
    q: Optional[str] = Query(None, description="按文件名模糊搜索"),
):
    """列出全部文档，支持按分类与文件名过滤。"""
    docs = doc_registry.list_docs()
    if category and category != "全部文档":
        docs = [d for d in docs if d.get("category") == category]
    if q:
        ql = q.lower()
        docs = [d for d in docs if ql in d.get("filename", "").lower()]

    items = [DocItem(**{k: d.get(k, "") for k in DocItem.model_fields}) for d in docs]
    return DocListResponse(total=len(items), items=items)


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: Optional[str] = Query(None, description="知识库分类"),
):
    """上传文档文件并导入知识库。"""
    if not file.filename:
        raise HTTPException(400, "文件名不能为空")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTS:
        raise HTTPException(
            400,
            f"不支持的文件格式: {suffix}，支持 {', '.join(sorted(SUPPORTED_EXTS))}",
        )

    filepath = UPLOAD_DIR / file.filename
    # 写入磁盘
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    size = filepath.stat().st_size

    # 导入向量库
    try:
        chunks = ingest_file(str(filepath))
    except Exception as e:
        # 清理已写入的物理文件
        try:
            filepath.unlink(missing_ok=True)
        except OSError:
            pass
        raise HTTPException(500, f"导入失败: {str(e)}")

    # 注册元数据
    record = doc_registry.register(
        filename=file.filename,
        source=str(filepath),
        chunks=chunks,
        category=category,
    )

    return UploadResponse(
        filename=file.filename,
        chunks=chunks,
        category=record["category"],
        size=size,
        message=f"成功导入 {chunks} 个文档片段",
    )


@router.post("/reindex")
async def reindex_documents(ids: List[str] = Query(..., description="待重索引的文档 id 列表")):
    """重新索引指定文档：先删除旧片段，再从磁盘重新导入。"""
    results = []
    for doc_id in ids:
        doc = doc_registry.get_doc(doc_id)
        if doc is None:
            results.append({"id": doc_id, "status": "not_found"})
            continue
        source = doc.get("source", "")
        p = Path(source)
        if not p.exists():
            results.append({"id": doc_id, "status": "file_missing"})
            continue
        # 先删旧片段
        _delete_chunks_by_source(source)
        # 再重新导入
        try:
            chunks = ingest_file(str(p))
            doc_registry.register(
                filename=doc.get("filename", p.name),
                source=source,
                chunks=chunks,
                category=doc.get("category"),
            )
            results.append({"id": doc_id, "status": "ok", "chunks": chunks})
        except Exception as e:
            results.append({"id": doc_id, "status": "error", "error": str(e)})

    return {"results": results}


@router.post("/batch-category")
async def batch_update_category(
    ids: List[str] = Query(..., description="待更新分类的文档 id 列表"),
    category: str = Query(..., description="新分类名称"),
):
    """批量更新文档分类。"""
    results = []
    for doc_id in ids:
        try:
            updated = doc_registry.update_category(doc_id, category)
            if updated:
                results.append({"id": doc_id, "status": "ok", "category": category})
            else:
                results.append({"id": doc_id, "status": "not_found"})
        except Exception as e:
            results.append({"id": doc_id, "status": "error", "error": str(e)})

    return {"results": results}


# ─── 参数化路径路由（放在最后避免干扰静态路径） ───

@router.get("/{doc_id}", response_model=DocDetailResponse)
async def get_document(doc_id: str):
    """文档详情，含正文与前若干个片段预览。"""
    doc = doc_registry.get_doc(doc_id)
    if doc is None:
        raise HTTPException(404, f"文档不存在: {doc_id}")

    source = doc.get("source", "")
    content = ""
    chunk_previews: List[ChunkPreview] = []

    # 优先读原始文件正文
    try:
        p = Path(source)
        if p.exists():
            content = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        pass

    # 从向量库取片段预览（最多 6 段）
    try:
        vs = get_vector_store()
        res = vs.get(where={"source": source}, include=["documents"])
        docs_text = res.get("documents", []) or []
        for i, text in enumerate(docs_text[:6]):
            chunk_previews.append(ChunkPreview(index=i + 1, text=text[:300]))
    except Exception as e:
        print(f"[documents] 读取片段预览失败: {e}")

    return DocDetailResponse(
        id=doc.get("id", ""),
        filename=doc.get("filename", ""),
        source=source,
        ext=doc.get("ext", "txt"),
        size=doc.get("size", 0),
        chunks=doc.get("chunks", len(chunk_previews)),
        category=doc.get("category", "未分类"),
        uploaded_at=doc.get("uploaded_at", ""),
        content=content[:4000],
        chunk_previews=chunk_previews,
    )


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档：移除元数据 + 删除向量片段 + 删除物理文件。"""
    doc = doc_registry.remove_doc(doc_id)
    if doc is None:
        raise HTTPException(404, f"文档不存在: {doc_id}")

    source = doc.get("source", "")
    deleted_chunks = _delete_chunks_by_source(source)

    # 删除物理文件（仅删除 uploads 目录下的，避免误删 knowledge 种子文件）
    try:
        p = Path(source)
        if p.exists() and "uploads" in p.parts:
            p.unlink()
    except OSError:
        pass

    return {
        "id": doc_id,
        "filename": doc.get("filename", ""),
        "deleted_chunks": deleted_chunks,
        "message": f"已删除 {doc.get('filename', '')}（{deleted_chunks} 个片段）",
    }
