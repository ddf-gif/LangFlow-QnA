"""角色管理 API — 创建 / 列表 / 删除。"""
from fastapi import APIRouter, HTTPException

from app.api.schemas import CreateRoleRequest, RoleItem, RoleListResponse
from app.services import roles

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("", response_model=RoleListResponse)
async def list_roles():
    """返回全部角色列表。"""
    items = roles.list_roles()
    return RoleListResponse(
        total=len(items),
        items=[RoleItem(**r) for r in items],
    )


@router.post("", response_model=RoleItem)
async def create_role(body: CreateRoleRequest):
    """创建一个新角色。"""
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "角色名称不能为空")
    record = roles.create_role(
        name=name,
        group=body.group,
        permissions=body.permissions,
        creator=body.creator,
    )
    return RoleItem(**record)


@router.delete("/{role_id}")
async def delete_role(role_id: str):
    """删除一个角色。"""
    record = roles.delete_role(role_id)
    if record is None:
        raise HTTPException(404, f"角色不存在: {role_id}")
    return {
        "id": role_id,
        "name": record.get("name", ""),
        "message": f"已删除角色「{record.get('name', '')}」",
    }
