from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class AttachmentResponse(BaseModel):
    """Attachment response"""
    id: UUID
    filename: str
    size: Optional[int]
    mime_type: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DraftCreate(BaseModel):
    """Draft creation request"""
    to_email: str
    cc: Optional[str] = None
    bcc: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "to_email": "recipient@example.com",
                "cc": "cc@example.com",
                "bcc": None,
                "subject": "Hello World",
                "body": "This is a draft email..."
            }
        }


class DraftUpdate(BaseModel):
    """Draft update request"""
    to_email: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Updated subject",
                "body": "Updated body content..."
            }
        }


class DraftResponse(BaseModel):
    """Draft response"""
    id: UUID
    user_id: UUID
    to_email: str
    cc: Optional[str]
    bcc: Optional[str]
    subject: Optional[str]
    body: Optional[str]
    attachments: List[AttachmentResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DraftListResponse(BaseModel):
    """Draft list response with pagination"""
    total: int
    skip: int
    limit: int
    drafts: List[DraftResponse]


class SendDraftRequest(BaseModel):
    """Send draft request"""
    pass  # No additional parameters needed


class EmailEvent(BaseModel):
    """Email event for RabbitMQ"""
    event_type: str  # email.send
    event_id: UUID
    timestamp: datetime
    user_id: UUID
    data: dict


class DraftSentResponse(BaseModel):
    """Response after sending draft"""
    success: bool
    message: str
    draft_id: UUID
    event_id: UUID
