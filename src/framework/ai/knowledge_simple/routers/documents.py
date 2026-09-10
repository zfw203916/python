# src/framework/ai/knowledge_simple/routers/documents.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Annotated
import uuid, anyio
from pathlib import Path

from ..database import KnowledgeDocument, KnowledgeChunk, get_db
from ..models import DocumentResponse
from ..services.document_service import DocumentService


router = APIRouter(prefix="/api/knowledge/documents", tags=["knowledge-documents"])
document_service = DocumentService()
UPLOAD_DIR = Path(__file__).parent.parent.parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 上传目录
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form()] = None,
    db: Annotated[Session, Depends(get_db)] = None
):
    """上传文档到知识库"""
    # 1. 检查文件类型
    filename = file.filename or "unknown"
    file_ext = filename.split(".")[-1].lower() if '.' in filename else 'txt'
    if file_ext not in ["pdf","docx", "txt"]:
        raise HTTPException(400,f"不支持的文件类型:{file_ext}")

    # 2. 保存临时文件
    safe_name = Path(filename).name
    safe_filename = f"{uuid.uuid4()}_{safe_name}" #uuid.uuid4() → 防止文件名冲突（并发安全）
    file_path = UPLOAD_DIR / safe_filename
    async with await anyio.open_file(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            await f.write(chunk)
 
    try:
        # 3. 提取文本
        content = document_service.extract_text_from_file(str(file_path),file_ext)
        # 检查是否提取成功
        if content.startswith(("⚠️","❌")):
            raise HTTPException(400, content)
        if not content or len(content.strip()) < 10:
            raise HTTPException(400, "文档内容为空或太短，请检查文件")
        # 4. 保存到知识库
        doc = document_service.save_document(
            db,
            title= title or filename,
            filename=safe_name,
            file_type=file_ext,
            content=content
        )
        return DocumentResponse(
            id = str(doc.id),
            title = doc.title,
            filename= doc.filename,
            file_type=doc.file_type,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at
        )
    finally:
        try:
            await anyio.Path(file_path).unlink()
        except FileNotFoundError:
            pass


@router.get("",response_model=List[DocumentResponse])
async def list_documents(db: Annotated[Session, Depends(get_db)]):
    """获取所有文档"""
    docs = db.query(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()).all()

    return [
        DocumentResponse(
            id=str(d.id),
            title=d.title,
            filename=d.filename,
            file_type=d.file_type,
            chunk_count=d.chunk_count,
            created_at=d.created_at
        ) 
        for d in docs
    ]


@router.delete("/{doc_id}",responses={404:{"description":"文档不存在"},400:{"description": "无效的文档ID"}})
async def delete_document(doc_id: str, db: Annotated[Session, Depends(get_db)]):
    """删除文档"""
    try:
        doc_uuid = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(400, "无效的文档ID")
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_uuid).first()
    if not doc:
        raise HTTPException(404, "文档不存在")
    
    # 删除关联的分块（由于设置了 cascade，会自动删除）
    db.delete(doc)
    db.commit()
    return {"message":"删除成功", "id": doc_id}