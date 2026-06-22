"""分类管理 API — 创建 / 列出已知分类。"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import doc_registry

router = APIRouter(prefix="/api/categories", tags=["categories"])


class CreateCategoryRequest(BaseModel):
    name: str


@router.get("")
async def list_categories():
    """返回已知分类名称列表。"""
    names = doc_registry.list_known_categories()
    return {"categories": names}


@router.post("")
async def create_category(body: CreateCategoryRequest):
    """创建一个新分类。"""
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "分类名称不能为空")
    ok = doc_registry.create_category(name)
    if not ok:
        raise HTTPException(409, f"分类「{name}」已存在")
    return {"name": name, "message": f"已创建分类「{name}」"}
