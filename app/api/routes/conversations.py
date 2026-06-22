"""对话记录 API — 列表 / 创建 / 查看 / 删除。"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.services import auth as auth_service
from app.services import conversations

router = APIRouter(prefix="/api/conversations", tags=["conversations"])
security = HTTPBearer(auto_error=False)


def _get_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None:
        raise HTTPException(401, "未登录")
    payload = auth_service.verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(401, "令牌无效")
    return payload["username"]


@router.get("")
async def list_conv(username: str = Depends(_get_user)):
    """列出当前用户的对话。"""
    items = conversations.list_conversations(username)
    return {"total": len(items), "items": items}


@router.post("")
async def create_conv(username: str = Depends(_get_user)):
    """创建新对话。"""
    conv = conversations.create_conversation(username)
    return conv


@router.get("/{conv_id}")
async def get_conv(conv_id: str, username: str = Depends(_get_user)):
    """查看单条对话的消息。"""
    conv = conversations.get_conversation(username, conv_id)
    if conv is None:
        raise HTTPException(404, "对话不存在")
    return conv


@router.delete("/{conv_id}")
async def delete_conv(conv_id: str, username: str = Depends(_get_user)):
    """删除对话。"""
    ok = conversations.delete_conversation(username, conv_id)
    if not ok:
        raise HTTPException(404, "对话不存在")
    return {"message": "已删除"}


class AddMessageRequest(BaseModel):
    role: str
    content: str


@router.post("/{conv_id}/messages")
async def add_message(conv_id: str, body: AddMessageRequest, username: str = Depends(_get_user)):
    """向对话追加一条消息。"""
    if body.role not in ("user", "assistant"):
        raise HTTPException(400, "role 必须为 user 或 assistant")
    conv = conversations.add_message(username, conv_id, body.role, body.content)
    if conv is None:
        raise HTTPException(404, "对话不存在")
    return {"message": "已添加"}
