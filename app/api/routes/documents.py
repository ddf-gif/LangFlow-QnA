"""文档上传 API。"""
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.ingestion.pipeline import ingest_file

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档文件并导入知识库。"""
    if not file.filename:
        raise HTTPException(400, "文件名不能为空")

    # 保存上传文件
    filepath = UPLOAD_DIR / file.filename
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 导入到向量库
    try:
        chunks = ingest_file(str(filepath))
        return {
            "filename": file.filename,
            "chunks": chunks,
            "message": f"成功导入 {chunks} 个文档片段",
        }
    except Exception as e:
        raise HTTPException(500, f"导入失败: {str(e)}")
