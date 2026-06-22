"""用户认证服务 — 注册 / 登录 / JWT 令牌管理。"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

USERS_PATH = Path("data/users.json")
USERS_PATH.parent.mkdir(parents=True, exist_ok=True)

# ─── 用户持久化 ───


def _load_users() -> Dict[str, Dict[str, Any]]:
    """加载全部用户（keyed by username）。"""
    if not USERS_PATH.exists():
        return {}
    try:
        return json.loads(USERS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_users(users: Dict[str, Dict[str, Any]]) -> None:
    """持久化用户数据。"""
    USERS_PATH.write_text(
        json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ─── 密码处理 ───


def hash_password(password: str) -> str:
    """对密码进行哈希。"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码。"""
    return pwd_context.verify(plain, hashed)


# ─── 用户管理 ───


def register_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """注册新用户。用户名已存在则返回 None。"""
    users = _load_users()
    if username in users:
        return None
    record = {
        "username": username,
        "password_hash": hash_password(password),
        "role": "user",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    users[username] = record
    _save_users(users)
    return {"username": username, "role": "user"}


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """验证用户名密码。成功返回用户信息，失败返回 None。

    同时检查固定管理员账号和 users.json 中的注册用户。
    """
    # 检查固定管理员账号
    if username == settings.admin_username and password == settings.admin_password:
        return {"username": username, "role": "admin"}
    # 检查注册用户
    users = _load_users()
    record = users.get(username)
    if record and verify_password(password, record.get("password_hash", "")):
        return {"username": username, "role": record.get("role", "user")}
    return None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """按用户名查询用户信息（不含密码哈希）。"""
    if username == settings.admin_username:
        return {"username": username, "role": "admin"}
    users = _load_users()
    record = users.get(username)
    if record:
        return {"username": username, "role": record.get("role", "user")}
    return None


# ─── JWT 令牌 ───


def create_token(username: str, role: str = "user") -> str:
    """签发 JWT 访问令牌。"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> Optional[Dict[str, str]]:
    """验证 JWT 令牌，返回 {username, role} 或 None。"""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        username = payload.get("sub")
        role = payload.get("role", "user")
        if username is None:
            return None
        return {"username": username, "role": role}
    except JWTError:
        return None
