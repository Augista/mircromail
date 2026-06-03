from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Draft(Base):
    """Draft email model"""
    __tablename__ = "drafts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    to_email = Column(String(255), nullable=False)
    cc = Column(String(500))
    bcc = Column(String(500))
    subject = Column(String(255))
    body = Column(String(50000))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attachments = relationship("Attachment", back_populates="draft", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_drafts_user_id', 'user_id'),
        Index('idx_drafts_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Draft(id={self.id}, user_id={self.user_id}, subject={self.subject})>"


class Attachment(Base):
    """Email attachment model"""
    __tablename__ = "attachments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    draft_id = Column(UUID(as_uuid=True), ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    size = Column(Integer)  # Size in bytes
    mime_type = Column(String(100))
    s3_key = Column(String(500))  # S3 or cloud storage key
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    draft = relationship("Draft", back_populates="attachments")
    
    # Indexes
    __table_args__ = (
        Index('idx_attachments_draft_id', 'draft_id'),
    )
    
    def __repr__(self):
        return f"<Attachment(id={self.id}, filename={self.filename})>"
