# my-test-framework/src/framework/ai/knowledge-base/services/document_parser.py
# 文档解析服务。 这个有点难。
import os
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
import pdfplumber
from docx import Document
import re
from loguru import logger

class DocumentParser:
    """企业级文档解析器"""
    # 支持的文件类型
    SUPPORTED_TYPES = {
        'txt':'text/plain',
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }

    MAX_CHUNK_SIZE = 500  # 字符数
    OVERLAP_SIZE = 50     # 重叠字符数

    @classmethod
    def parse_file(cls, file_content: bytes, filename: str) -> Dict[str, Any]:
        """解析文档，返回结构化数据"""
        print(f"🔍 开始解析: {filename}")  # ← 加在这里
        ext = filename.split(".")[-1].lower()
        if ext not in cls.SUPPORTED_TYPES:
            raise ValueError("不支持的文件格式{ext}")

        # 计算文件哈希
        file_hash = hashlib.sha256(file_content).hexdigest()
        chunks = []
        metadata = {
            'filename': filename,
            'file_type': ext,
            'file_size': len(file_content),
            'file_hash': file_hash
        }

        if ext == 'txt':
            text = file_content.decode('utf-8', errors= 'ignore')
            chunks = cls._chunk_text(text, filename)
            metadata['page_count'] = 1
            metadata['world_count'] = len(text.split())

        elif ext == 'pdf':
            chunks, pdf_metadata = cls._pare_pdf(file_content, filename)
            metadata.update(pdf_metadata)
        elif ext in ['doc','docx']:
            chunks, doc_metadata = cls._pare_doc(file_content, filename)
            metadata.update(doc_metadata)

        return {
            'chunks':chunks,
            'metadata': metadata,
            'chunk_count': len(chunks)
        }


    @staticmethod
    def _pare_pdf(file_content: bytes, filename: str) -> tuple:
        """解析PDF文件"""
        chunks = []
        metadata = {'page_count': 0, 'world_count': 0}
        with tempfile.NamedTemporaryFile(delete=True, suffix='.pdf') as tmp_file:
            tmp_file.write(file_content)
            tmp_file.flush()
            with pdfplumber.open(tmp_file.name) as pdf:
                tmp_file['page_count'] = len(pdf.pages)
                full_text = ''
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        full_text += f"\n\n[第{page_num + 1}页]\n{page_text}"
                metadata['word_count'] = len(full_text.split())

                if full_text.strip():
                    chunks = DocumentParser.__chunk_text(full_text, filename)

        return chunks, metadata
                    


    @staticmethod
    def _parse_docx(file_content: bytes, filename: str) -> tuple:
        """解析DOCX文件"""
        chunks = []
        metadata = {'page_count': 0, 'world_count': 0}
        with tempfile.NamedTemporaryFile(delete=True, suffix='.docx') as tmp_file:
            tmp_file.write(file_content)
            tmp_file.flush()
            doc = Document(tmp_file.name)
            full_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            metadata['world_count'] = len(full_text.split())
            metadata['page_count'] = 1
            if full_text.strip():
                chunks = DocumentParser._chunk_text(full_text, filename)

        return chunks, metadata


    @staticmethod
    def _chunk_text(text: bytes, filename: str) -> List[Dict[str, Any]]:
        """智能切分文本 - 保留语义完整性"""
        chunks = []
        # 1. 按段落分割
        paragraphs = text.split('\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        current_chunk = []
        current_size = 0
        for para in paragraphs:
            para_size = len(para)
            # 如果单个段落超过最大大小，强制拆分
            if para.size > DocumentParser.MAX_CHUNK_SIZE:
                # 保存当前chunk
                if current_chunk:
                    chunks.append(DocumentParser._create_chunk(current_chunk, filename, len(chunks)))
                    # 保留重叠部分（最后一段）
                    if DocumentParser.OVERLAP_SIZE > 0 and current_chunk:
                        overlap_text = current_chunk[-1]
                        current_chunk = [overlap_text]
                        current_size = len(overlap_text)
                    else:
                        current_chunk = []
                        current_size = 0

                    current_chunk.append(para)
                    current_size += para_size
                    # 处理最后一个chunk
                    if current_chunk:
                        chunks.append(DocumentParser._create_chunk(current_chunk, filename, len(chunks)))

        return chunks
            




    @staticmethod
    def _split_long_paragraph(text: str, filename: str, start_index: int) -> List[Dict[str, Any]]:
        """拆分超长段落"""
        chunks = []
        sentences = re.split(r'(?<=[。！？；])', text)
        
        current_chunk = []
        current_size = 0
        for sentence in sentences:
            if not sentence.strip():
                continue
            if current_size + len(sentence)  > DocumentParser.MAX_CHUNK_SIZE and current_chunk:
                chunks.append(DocumentParser._create_chunk(current_chunk, filename, start_index + len(chunks)))
                current_chunk = [sentence]
                current_size = len(sentence)
            else:
                current_chunk.append(sentence)
                current_size += len(sentence)

        if current_chunk:
            chunks.append(DocumentParser._create_chunk(current_chunk, filename, start_index + len(chunks)))

        return  chunks


    @staticmethod
    def _create_chunk(paragraphs: List[str], filename: str, index: int) -> List[Dict[str, Any]]:
        """创建chunk对象"""
        content = '\n'.join(paragraphs)
        return {
            'content': content,
            'chunk_index': index,
            'source_file': filename,
            'metadata':{
                'char_count': len(content),
                'paragraph_count': len(paragraphs),
                'word_count': len(content.split()),
            }
        }
