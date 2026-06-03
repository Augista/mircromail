"""
MicroMail Mail Storage Service
Handles email storage and retrieval (CQRS pattern)
Read model for listing emails
Write model for storing emails from delivery service
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from enum import Enum
import os
import json
import pika
from typing import Optional

app = FastAPI(title="Mail Storage Service", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RabbitMQ configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

# Mock database - will be replaced with PostgreSQL
emails_db: dict = {}


# ============ Models ============

class EmailFolder(str, Enum):
    INBOX = "inbox"
    SENT = "sent"
    TRASH = "trash"
    ARCHIVE = "archive"


class EmailResponse(BaseModel):
    id: str
    from_email: str
    from_name: str
    to: str
    cc: Optional[list[str]]
    bcc: Optional[list[str]]
    subject: str
    preview: str
    timestamp: str
    read: bool
    folder: EmailFolder
    has_attachments: bool


class EmailDetailResponse(BaseModel):
    id: str
    from_email: str
    from_name: str
    to: str
    cc: Optional[list[str]]
    bcc: Optional[list[str]]
    subject: str
    body: str
    timestamp: str
    read: bool
    folder: EmailFolder
    labels: list[str]
    attachments: list[dict]


class EmailListResponse(BaseModel):
    emails: list[EmailResponse]
    total: int
    page: int
    limit: int
    unread_count: int


# ============ Helper Functions ============

def get_connection():
    """Get RabbitMQ connection"""
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        return connection
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Failed to connect to RabbitMQ: {e}")
        return None


def subscribe_to_events():
    """Subscribe to email events from RabbitMQ (would run in background)"""
    try:
        connection = get_connection()
        if not connection:
            return
        
        channel = connection.channel()
        
        # Declare exchange
        channel.exchange_declare(
            exchange="micromail",
            exchange_type="topic",
            durable=True
        )
        
        # Create queue for this service
        queue = channel.queue_declare(queue="storage-service", durable=True)
        
        # Bind to email events
        channel.queue_bind(
            exchange="micromail",
            queue="storage-service",
            routing_key="email.delivered"
        )
        
        # Consume messages
        channel.basic_consume(
            queue="storage-service",
            on_message_callback=handle_email_event,
            auto_ack=True
        )
        
        print("Storage service listening for email events...")
        channel.start_consuming()
    except Exception as e:
        print(f"Error subscribing to events: {str(e)}")


def handle_email_event(ch, method, properties, body):
    """Handle incoming email events from RabbitMQ"""
    try:
        event_data = json.loads(body)
        print(f"Storage service received event: {event_data}")
        
        # Store email in database
        email_id = event_data.get("email_id")
        emails_db[email_id] = event_data
    except Exception as e:
        print(f"Error handling email event: {str(e)}")


# ============ API Endpoints ============

@app.post("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "storage"}


@app.get("/inbox", response_model=EmailListResponse)
async def list_inbox(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("timestamp"),
    order: str = Query("desc", regex="^(asc|desc)$")
):
    """
    List emails in the inbox (Read model)
    """
    user_id = "user_123"  # Extract from token
    
    # Filter inbox emails
    inbox_emails = [
        e for e in emails_db.values()
        if e.get("user_id") == user_id and e.get("folder") == "inbox"
    ]
    
    # Sort
    reverse = order == "desc"
    if sort == "timestamp":
        inbox_emails.sort(key=lambda x: x.get("timestamp", ""), reverse=reverse)
    elif sort == "from":
        inbox_emails.sort(key=lambda x: x.get("from_name", ""), reverse=reverse)
    elif sort == "subject":
        inbox_emails.sort(key=lambda x: x.get("subject", ""), reverse=reverse)
    
    # Count unread
    unread_count = sum(1 for e in inbox_emails if not e.get("read", False))
    
    # Pagination
    start = (page - 1) * limit
    end = start + limit
    paginated = inbox_emails[start:end]
    
    # Convert to response format
    emails = [
        EmailResponse(
            id=e["id"],
            from_email=e.get("from_email", ""),
            from_name=e.get("from_name", ""),
            to=e.get("to", ""),
            cc=e.get("cc"),
            bcc=e.get("bcc"),
            subject=e.get("subject", ""),
            preview=e.get("preview", e.get("body", "")[:100]),
            timestamp=e.get("timestamp", ""),
            read=e.get("read", False),
            folder=EmailFolder.INBOX,
            has_attachments=len(e.get("attachments", [])) > 0
        )
        for e in paginated
    ]
    
    return EmailListResponse(
        emails=emails,
        total=len(inbox_emails),
        page=page,
        limit=limit,
        unread_count=unread_count
    )


@app.get("/sent", response_model=EmailListResponse)
async def list_sent(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    List emails in the sent folder
    """
    user_id = "user_123"  # Extract from token
    
    # Filter sent emails
    sent_emails = [
        e for e in emails_db.values()
        if e.get("user_id") == user_id and e.get("folder") == "sent"
    ]
    
    # Sort by timestamp (newest first)
    sent_emails.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Pagination
    start = (page - 1) * limit
    end = start + limit
    paginated = sent_emails[start:end]
    
    # Convert to response format
    emails = [
        EmailResponse(
            id=e["id"],
            from_email=e.get("from_email", ""),
            from_name=e.get("from_name", ""),
            to=e.get("to", ""),
            cc=e.get("cc"),
            bcc=e.get("bcc"),
            subject=e.get("subject", ""),
            preview=e.get("preview", e.get("body", "")[:100]),
            timestamp=e.get("timestamp", ""),
            read=True,  # Sent emails are always read
            folder=EmailFolder.SENT,
            has_attachments=len(e.get("attachments", [])) > 0
        )
        for e in paginated
    ]
    
    return EmailListResponse(
        emails=emails,
        total=len(sent_emails),
        page=page,
        limit=limit,
        unread_count=0
    )


@app.get("/trash", response_model=EmailListResponse)
async def list_trash(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    List emails in the trash folder
    """
    user_id = "user_123"  # Extract from token
    
    # Filter trash emails
    trash_emails = [
        e for e in emails_db.values()
        if e.get("user_id") == user_id and e.get("folder") == "trash"
    ]
    
    # Sort by timestamp (newest first)
    trash_emails.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Pagination
    start = (page - 1) * limit
    end = start + limit
    paginated = trash_emails[start:end]
    
    # Convert to response format
    emails = [
        EmailResponse(
            id=e["id"],
            from_email=e.get("from_email", ""),
            from_name=e.get("from_name", ""),
            to=e.get("to", ""),
            cc=e.get("cc"),
            bcc=e.get("bcc"),
            subject=e.get("subject", ""),
            preview=e.get("preview", e.get("body", "")[:100]),
            timestamp=e.get("timestamp", ""),
            read=e.get("read", False),
            folder=EmailFolder.TRASH,
            has_attachments=len(e.get("attachments", [])) > 0
        )
        for e in paginated
    ]
    
    return EmailListResponse(
        emails=emails,
        total=len(trash_emails),
        page=page,
        limit=limit,
        unread_count=0
    )


@app.get("/emails/{email_id}", response_model=EmailDetailResponse)
async def get_email(email_id: str):
    """
    Get full details of a specific email
    """
    email = emails_db.get(email_id)
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return EmailDetailResponse(
        id=email["id"],
        from_email=email.get("from_email", ""),
        from_name=email.get("from_name", ""),
        to=email.get("to", ""),
        cc=email.get("cc"),
        bcc=email.get("bcc"),
        subject=email.get("subject", ""),
        body=email.get("body", ""),
        timestamp=email.get("timestamp", ""),
        read=email.get("read", False),
        folder=EmailFolder(email.get("folder", "inbox")),
        labels=email.get("labels", []),
        attachments=email.get("attachments", [])
    )


@app.get("/search")
async def search_emails(
    q: str = Query(..., min_length=1),
    folder: Optional[str] = None,
    from_email: Optional[str] = None,
    to: Optional[str] = None,
    before: Optional[str] = None,
    after: Optional[str] = None
):
    """
    Search emails with filters
    """
    user_id = "user_123"  # Extract from token
    
    # Start with all user emails
    results = [e for e in emails_db.values() if e.get("user_id") == user_id]
    
    # Filter by query
    query = q.lower()
    results = [
        e for e in results
        if query in e.get("subject", "").lower()
        or query in e.get("body", "").lower()
        or query in e.get("from_name", "").lower()
    ]
    
    # Apply filters
    if folder:
        results = [e for e in results if e.get("folder") == folder]
    
    if from_email:
        results = [e for e in results if from_email.lower() in e.get("from_email", "").lower()]
    
    if to:
        results = [e for e in results if to.lower() in e.get("to", "").lower()]
    
    # Date filtering (simplified)
    if before:
        results = [e for e in results if e.get("timestamp", "") <= before]
    
    if after:
        results = [e for e in results if e.get("timestamp", "") >= after]
    
    return {
        "emails": [
            {
                "id": e["id"],
                "from": e.get("from_name", ""),
                "subject": e.get("subject", ""),
                "preview": e.get("preview", ""),
                "timestamp": e.get("timestamp", "")
            }
            for e in results
        ],
        "total": len(results),
        "query": q
    }


@app.delete("/emails/{email_id}")
async def delete_email(email_id: str):
    """
    Delete an email (move to trash or permanently delete if already in trash)
    """
    email = emails_db.get(email_id)
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # If in trash, permanently delete
    if email.get("folder") == "trash":
        del emails_db[email_id]
    else:
        # Move to trash
        email["folder"] = "trash"
        emails_db[email_id] = email
    
    return {"status": "ok", "message": "Email deleted successfully"}


@app.post("/emails/{email_id}/mark-read")
async def mark_email_read(email_id: str, read: bool = True):
    """
    Mark an email as read/unread
    """
    email = emails_db.get(email_id)
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email["read"] = read
    emails_db[email_id] = email
    
    return {"status": "ok", "message": f"Email marked as {'read' if read else 'unread'}"}


if __name__ == "__main__":
    import uvicorn
    # In a real implementation, run event subscriber in a separate thread
    # import threading
    # threading.Thread(target=subscribe_to_events, daemon=True).start()
    
    uvicorn.run(app, host="0.0.0.0", port=8003)
