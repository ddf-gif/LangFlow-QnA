"""
文档元数据注册表（JSON 存储）。

为什么需要它？
    Chroma 中的 chunk id 是随机 UUID，且同一文件多次入库会产生重复 chunk。
    无法按"文档"维度查询或删除。这里用一个 JSON 清单维护每个源文件的
    元数据（文件名、入库路径、片段数、大小、分类、上传时间），并提供
    按 source 过滤删除向量片段的能力。

数据文件：data/doc_registry.json
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

REGISTRY_PATH = Path("data/doc_registry.json")
CATEGORIES_PATH = Path("data/categories.json")
REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)


def _doc_id(source: str) -> str:
    """文档 id 取源路径的 basename（去扩展名）。"""
    name = Path(source).name
    return Path(name).stem


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _read_file_size(source: str) -> int:
    """从文件系统读取文件大小，读不到返回 0。"""
    try:
        p = Path(source)
        if p.exists():
            return p.stat().st_size
    except OSError:
        pass
    return 0


def load_all() -> List[Dict[str, Any]]:
    """加载全部文档记录。文件不存在则返回空列表。"""
    if not REGISTRY_PATH.exists():
        return []
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_all(docs: List[Dict[str, Any]]) -> None:
    """持久化全部记录。"""
    REGISTRY_PATH.write_text(
        json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def list_docs() -> List[Dict[str, Any]]:
    """返回全部文档记录（按上传时间倒序）。"""
    docs = load_all()
    docs.sort(key=lambda d: d.get("uploaded_at", ""), reverse=True)
    return docs


def get_doc(doc_id: str) -> Optional[Dict[str, Any]]:
    """按 id 取单条记录。"""
    for d in load_all():
        if d.get("id") == doc_id:
            return d
    return None


def _guess_category(filename: str, existing: Dict[str, str]) -> str:
    """根据文件名启发式猜测分类；无法判定时归为「未分类」。"""
    name = filename.lower()
    if "财务" in name or "finance" in name or "年报" in name or "营收" in name:
        return "财务报告"
    if "人力" in name or "hr" in name or "员工" in name or "培训" in name:
        return "人力资源"
    if "技术" in name or "api" in name or "agent" in name or "开发" in name:
        return "技术文档"
    if "法务" in name or "合规" in name or "legal" in name:
        return "法务合规"
    if "产品" in name or "product" in name:
        return "产品手册"
    # 同名已有记录则沿用其分类
    return existing.get(_doc_id(filename), "未分类")


def register(
    filename: str,
    source: str,
    chunks: int,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    注册（或更新）一条文档记录。

    若同名文档已存在，则更新其元数据（片段数、大小、上传时间）。
    """
    docs = load_all()
    by_id = {d["id"]: d for d in docs}
    doc_id = _doc_id(source)

    existing_cat = {d["id"]: d.get("category", "未分类") for d in docs}
    record = {
        "id": doc_id,
        "filename": filename,
        "source": str(source),
        "ext": Path(filename).suffix.lstrip(".").lower() or "txt",
        "size": _read_file_size(source),
        "chunks": chunks,
        "category": category or _guess_category(filename, existing_cat),
        "uploaded_at": _now_iso(),
    }

    # 覆盖同 id 记录，保持顺序：先移除旧的再追加新的
    docs = [d for d in docs if d["id"] != doc_id]
    docs.append(record)
    save_all(docs)
    return record


def remove_doc(doc_id: str) -> Optional[Dict[str, Any]]:
    """删除一条记录，返回被删除的记录（不存在则 None）。"""
    docs = load_all()
    target = next((d for d in docs if d.get("id") == doc_id), None)
    if target is None:
        return None
    docs = [d for d in docs if d.get("id") != doc_id]
    save_all(docs)
    return target


def update_category(doc_id: str, category: str) -> Optional[Dict[str, Any]]:
    """更新文档分类，返回更新后的记录（不存在则 None）。"""
    docs = load_all()
    target = next((d for d in docs if d.get("id") == doc_id), None)
    if target is None:
        return None
    target["category"] = category
    save_all(docs)
    return target


def migrate_from_vector_store() -> List[Dict[str, Any]]:
    """
    首次启动时从向量库扫描已存在的 chunk，按 source basename 聚合，
    生成初始文档清单。仅当注册表为空时执行，且仅执行一次。

    返回生成（或已有）的记录列表。
    """
    docs = load_all()
    if docs:
        return docs

    # 懒加载向量库（首次会触发 embedding 模型加载）
    try:
        from app.retrieval.vector_store import get_vector_store

        vs = get_vector_store()
        res = vs.get(include=["metadatas", "documents"])
    except Exception as e:  # 向量库未初始化或为空
        print(f"[doc_registry] 扫描向量库失败: {e}")
        return []

    ids = res.get("ids", [])
    metadatas = res.get("metadatas", [])
    documents = res.get("documents", [])

    # 按 source 聚合：每个 source -> [chunk 文本...]
    grouped: Dict[str, List[str]] = {}
    for i, meta in enumerate(metadatas or []):
        source = (meta or {}).get("source", f"unknown_{i}")
        grouped.setdefault(source, []).append(documents[i] if i < len(documents) else "")

    # 同名文件（不同路径）会产生相同的 doc_id（basename stem）。
    # 这里按 doc_id 合并：保留首个 source 路径，chunks 累加，
    # 避免出现重复 id 导致删除时定位不到。
    merged: Dict[str, Dict[str, Any]] = {}
    for source, chunks_text in grouped.items():
        filename = Path(source).name
        doc_id = _doc_id(source)
        if doc_id in merged:
            merged[doc_id]["chunks"] += len(chunks_text)
            continue
        merged[doc_id] = {
            "id": doc_id,
            "filename": filename,
            "source": str(source),
            "ext": Path(filename).suffix.lstrip(".").lower() or "txt",
            "size": _read_file_size(source),
            "chunks": len(chunks_text),
            "category": _guess_category(filename, {}),
            "uploaded_at": _now_iso(),
        }

    records: List[Dict[str, Any]] = list(merged.values())

    save_all(records)
    print(f"[doc_registry] 自动迁移完成：发现 {len(records)} 个文档")
    return records


def get_categories() -> List[Dict[str, Any]]:
    """返回分类列表及每个分类的文档数 / 片段数（供目录树与统计使用）。

    包含所有已知分类（即使文档数为 0）及文档中出现的其他分类（如"未分类"）。
    """
    # 从所有已知分类开始（含 0 文档的分类）
    stats: Dict[str, Dict[str, int]] = {}
    for name in _load_categories():
        stats[name] = {"count": 0, "chunks": 0}
    # 统计文档中各分类的实际数量
    docs = load_all()
    for d in docs:
        cat = d.get("category", "未分类")
        if cat not in stats:
            stats[cat] = {"count": 0, "chunks": 0}
        stats[cat]["count"] += 1
        stats[cat]["chunks"] += d.get("chunks", 0)
    return [{"name": k, "count": v["count"], "chunks": v["chunks"]} for k, v in stats.items()]


# ─── 分类管理 ───

_DEFAULT_CATEGORIES = ["财务报告", "人力资源", "技术文档", "法务合规", "产品手册"]


def _load_categories() -> List[str]:
    """从文件加载已知分类列表。"""
    if not CATEGORIES_PATH.exists():
        _save_categories(_DEFAULT_CATEGORIES)
        return _DEFAULT_CATEGORIES.copy()
    try:
        data = json.loads(CATEGORIES_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return _DEFAULT_CATEGORIES.copy()


def _save_categories(cats: List[str]) -> None:
    """持久化已知分类列表。"""
    CATEGORIES_PATH.write_text(
        json.dumps(cats, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def list_known_categories() -> List[str]:
    """返回已知分类名称列表。"""
    return _load_categories()


def create_category(name: str) -> bool:
    """创建一个新分类。已存在则返回 False。"""
    name = name.strip()
    if not name:
        return False
    cats = _load_categories()
    if name in cats:
        return False
    cats.append(name)
    _save_categories(cats)
    return True
