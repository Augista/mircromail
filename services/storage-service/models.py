from sqlalchemy import Column, String, DateTime, Boolean, Index, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class Email(Base):
    """Email model - CQRS read model"""
    __tablename__ = "emails"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255))
    to_email = Column(String(255), nullable=False)
    cc = Column(String(500))
    bcc = Column(String(500))
    subject = Column(String(255), nullable=False)
    body = Column(Text)  # Full email body for full-text search
    preview = Column(String(500))  # Preview text
    folder = Column(
        String(50),
        default='inbox',
        nullable=False,
        index=True
    )
    is_read = Column(Boolean, default=False, index=True)
    is_starred = Column(Boolean, default=False)
    labels = Column(ARRAY(String(100)), default=list)
    timestamp = Column(DateTime, nullable=False)  # When email was sent/received
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for fast queries
    __table_args__ = (
        Index('idx_emails_user_id_folder', 'user_id', 'folder'),
        Index('idx_emails_user_id_timestamp', 'user_id', 'timestamp'),
        Index('idx_emails_user_id_read', 'user_id', 'is_read'),
        Index('idx_emails_search', 'to_tsvector("english", subject || " " || body)', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<Email(id={self.id}, from={self.from_email}, subject={self.subject})>"
