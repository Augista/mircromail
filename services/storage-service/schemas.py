from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class EmailResponse(BaseModel):
    """Email response"""
    id: UUID
    from_email: str
    from_name: Optional[str]
    to_email: str
    cc: Optional[str]
    bcc: Optional[str]
    subject: str
    preview: Optional[str]
    folder: str
    is_read: bool
    is_starred: bool
    labels: List[str]
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmailListResponse(BaseModel):
    """Email list response with pagination"""
    total: int
    skip: int
    limit: int
    emails: List[EmailResponse]


class EmailDetailResponse(BaseModel):
    """Email detail with full body"""
    id: UUID
    from_email: str
    from_name: Optional[str]
    to_email: str
    cc: Optional[str]
    bcc: Optional[str]
    subject: str
    body: Optional[str]  # Full body only in detail view
    folder: str
    is_read: bool
    is_starred: bool
    labels: List[str]
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class MarkReadRequest(BaseModel):
    """Mark email as read request"""
    is_read: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_read": True
            }
        }


class SearchRequest(BaseModel):
    """Search emails request"""
    query: str
    folder: Optional[str] = None
    skip: int = 0
    limit: int = 50


class SearchResponse(BaseModel):
    """Search response"""
    total: int
    query: str
    results: List[EmailResponse]


class EmailStoredEvent(BaseModel):
    """Email stored event from RabbitMQ"""
    event_type: str
    event_id: UUID
    timestamp: datetime
    user_id: UUID
    data: dict
