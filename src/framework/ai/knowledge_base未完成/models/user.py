# my-test-framework/src/framework/ai/knowledge-base/models/user.py
from sqlalchemy import Column, String, DateTime, Boolean, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from passlib.context import CryptContext
from ..database import Base


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    """用户模型 - 企业级认证"""
    __tablename__ = "kb_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    department = Column(String(50))
    role = Column(Enum("admin", "manger", "membber", "viewer", name="user_role"), default="membber")
    s_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = Column(DateTime)
    preferences = Column(JSON, default={})

    # 关系
    knowledge_bases =  relationship("KnowledgeBase", back_populates="owner")
    documents = relationship("Document", back_populates="uploader")
    audit_logs = relationship("AuditLog", back_populates="user")

    def set_password(self, password: str):
        self.hashed_password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

    def to_dict(self):
        return {
            'id': str(self.id),
            'username':self.username,
            'email': self.email,
            'full_name': self.full_name,
            'department': self.department,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }


class Team(Base):
    """团队模型 - 多租户支持"""
    __tablename__ = "kb_teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)

   # 关系
    members =  relationship("TeamMember", back_populates="team")
    knowledge_bases = relationship("KnowledgeBase", back_populates="team")

class TeamMember(Base):
    """团队成员"""
    __tablename__ = "kb_team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(Enum('admin', 'member', 'viewer', name='team_role'), default='member')
    joined_at = Column(DateTime, default=datetime.now)

    team = relationship("Team", back_populates="members")