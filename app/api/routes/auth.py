"""用户认证 API — 注册 / 登录 / 当前用户查询。"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.services import auth

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


def _get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """从 JWT 令牌中解析当前用户。"""
    if credentials is None:
        raise HTTPException(401, "未提供认证令牌")
    payload = auth.verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(401, "令牌无效或已过期")
    return payload


@router.post("/register")
async def register(body: RegisterRequest):
    """注册新用户。"""
    username = body.username.strip()
    password = body.password.strip()
    if not username or len(username) < 2:
        raise HTTPException(400, "用户名至少 2 个字符")
    if not password or len(password) < 4:
        raise HTTPException(400, "密码至少 4 个字符")
    if username == auth.settings.admin_username:
        raise HTTPException(400, "该用户名已被保留")
    result = auth.register_user(username, password)
    if result is None:
        raise HTTPException(409, "用户名已存在")
    token = auth.create_token(result["username"], result["role"])
    return {"username": result["username"], "token": token, "message": "注册成功"}


@router.post("/login")
async def login(body: LoginRequest):
    """用户登录，返回 JWT 令牌。"""
    username = body.username.strip()
    password = body.password.strip()
    if not username or not password:
        raise HTTPException(400, "用户名和密码不能为空")
    user = auth.authenticate_user(username, password)
    if user is None:
        raise HTTPException(401, "用户名或密码错误")
    token = auth.create_token(user["username"], user["role"])
    return {
        "username": user["username"],
        "role": user["role"],
        "token": token,
        "message": "登录成功",
    }


@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """获取当前登录用户信息。"""
    payload = _get_current_user(credentials)
    return {
        "username": payload["username"],
        "role": payload["role"],
    }
