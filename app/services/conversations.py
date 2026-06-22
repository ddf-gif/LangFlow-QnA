"""
对话记录管理 — JSON 持久化存储。

数据文件：data/conversations.json
结构：{username: [{id, title, created_at, updated_at, messages: [{role, content}]}]}
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_PATH = Path("data/conversations.json")
DATA_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_all() -> Dict[str, List[Dict[str, Any]]]:
    if not DATA_PATH.exists():
        return {}
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_all(data: Dict[str, List[Dict[str, Any]]]) -> None:
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _next_id(convs: List[Dict[str, Any]]) -> str:
    max_n = 0
    for c in convs:
        cid = c.get("id", "")
        if cid.startswith("conv-"):
            try:
                n = int(cid[5:])
                if n > max_n:
                    max_n = n
            except ValueError:
                pass
    return f"conv-{max_n + 1}"


def list_conversations(username: str) -> List[Dict[str, Any]]:
    """返回用户的对话列表（不含消息体），按更新时间倒序。"""
    data = _load_all()
    convs = data.get(username, [])
    convs = [
        {"id": c["id"], "title": c.get("title", "新对话"), "created_at": c.get("created_at", ""), "updated_at": c.get("updated_at", "")}
        for c in convs
    ]
    convs.sort(key=lambda c: c.get("updated_at", ""), reverse=True)
    return convs


def get_conversation(username: str, conv_id: str) -> Optional[Dict[str, Any]]:
    """返回单条对话（含消息）。"""
    data = _load_all()
    for c in data.get(username, []):
        if c["id"] == conv_id:
            return c
    return None


def create_conversation(username: str, title: str = "新对话") -> Dict[str, Any]:
    """创建新对话。"""
    data = _load_all()
    if username not in data:
        data[username] = []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conv = {
        "id": _next_id(data[username]),
        "title": title,
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }
    data[username].insert(0, conv)
    _save_all(data)
    return conv


def add_message(username: str, conv_id: str, role: str, content: str) -> Optional[Dict[str, Any]]:
    """向对话追加一条消息。"""
    data = _load_all()
    for c in data.get(username, []):
        if c["id"] == conv_id:
            c.setdefault("messages", []).append({
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
            c["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            # 自动用第一条用户消息做标题
            if role == "user" and c.get("title", "新对话") == "新对话":
                c["title"] = content[:30] + ("…" if len(content) > 30 else "")
            _save_all(data)
            return c
    return None


def delete_conversation(username: str, conv_id: str) -> bool:
    """删除对话。"""
    data = _load_all()
    if username not in data:
        return False
    before = len(data[username])
    data[username] = [c for c in data[username] if c["id"] != conv_id]
    if len(data[username]) == before:
        return False
    _save_all(data)
    return True
