# my-test-framework/src/framework/ai/knowledge-base/models/audit_log.py

from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from ..database import Base
from sqlalchemy.orm import relationship

class AuditLog(Base):
    """审计日志 - 企业级合规"""
    __tablename__ = "kb_audit_logs"

    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # upload, delete, search, update, view
    resource_type = Column(String(50))  # document, knowledge_base, user
    resource_id = Column(UUID(as_uuid=True))
    resource_name = Column(String(200))
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    details = Column(JSON, default={})
    status = Column(String(20))  # success, failure
    error_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.now, index=True)

    # 关系
    user = relationship("User", back_populates="audit_logs")
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': str(self.resource_id) if self.resource_id else None,
            'resource_name': self.resource_name,
            'ip_address': self.ip_address,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }