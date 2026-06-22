"""
角色管理服务 — JSON 持久化存储。

数据文件：data/roles.json
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

ROLES_PATH = Path("data/roles.json")
ROLES_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_all() -> List[Dict[str, Any]]:
    """加载全部角色记录。文件不存在则返回空列表。"""
    if not ROLES_PATH.exists():
        return []
    try:
        return json.loads(ROLES_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save_all(roles: List[Dict[str, Any]]) -> None:
    """持久化全部记录。"""
    ROLES_PATH.write_text(
        json.dumps(roles, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _next_id(roles: List[Dict[str, Any]]) -> str:
    """生成自增 id：role-1, role-2, ..."""
    max_n = 0
    for r in roles:
        rid = r.get("id", "")
        if rid.startswith("role-"):
            try:
                n = int(rid[5:])
                if n > max_n:
                    max_n = n
            except ValueError:
                pass
    return f"role-{max_n + 1}"


def list_roles() -> List[Dict[str, Any]]:
    """返回全部角色记录。"""
    return _load_all()


def create_role(
    name: str,
    group: str = "编辑者",
    permissions: str = "",
    creator: str = "当前用户",
) -> Dict[str, Any]:
    """创建一个新角色。"""
    roles = _load_all()
    now = __import__("datetime").datetime.now().isoformat(timespec="seconds")[:10]
    record = {
        "id": _next_id(roles),
        "name": name,
        "group": group,
        "permissions": permissions,
        "creator": creator,
        "created_at": now,
    }
    roles.append(record)
    _save_all(roles)
    return record


def delete_role(role_id: str) -> Optional[Dict[str, Any]]:
    """删除一个角色，返回被删除的记录（不存在则 None）。"""
    roles = _load_all()
    target = next((r for r in roles if r.get("id") == role_id), None)
    if target is None:
        return None
    roles = [r for r in roles if r.get("id") != role_id]
    _save_all(roles)
    return target
