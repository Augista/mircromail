"""
MicroMail Mail Composer Service
Handles email draft creation, editing, and sending
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
import os
import uuid
import json
import pika

app = FastAPI(title="Mail Composer Service", version="1.0.0")

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
drafts_db: dict = {}


# ============ Request/Response Models ============

class DraftCreate(BaseModel):
    to: EmailStr
    subject: str
    body: str
    cc: list[EmailStr] | None = None
    bcc: list[EmailStr] | None = None
    attachments: list[str] | None = None


class DraftUpdate(BaseModel):
    to: EmailStr | None = None
    subject: str | None = None
    body: str | None = None
    cc: list[EmailStr] | None = None
    bcc: list[EmailStr] | None = None


class DraftResponse(BaseModel):
    id: str
    user_id: str
    to: EmailStr
    subject: str
    body: str
    cc: list[EmailStr] | None
    bcc: list[EmailStr] | None
    created_at: str
    updated_at: str
    attachments: list[dict] | None = None


class DraftListResponse(BaseModel):
    drafts: list[DraftResponse]
    total: int
    page: int
    limit: int


# ============ Helper Functions ============

def get_connection():
    """Get RabbitMQ connection"""
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        return connection
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Failed to connect to RabbitMQ: {e}")
        return None


def publish_event(event_name: str, data: dict):
    """Publish an event to RabbitMQ"""
    try:
        connection = get_connection()
        if not connection:
            print(f"Warning: Could not publish event {event_name}")
            return
        
        channel = connection.channel()
        
        # Declare exchange
        channel.exchange_declare(
            exchange="micromail",
            exchange_type="topic",
            durable=True
        )
        
        # Publish message
        channel.basic_publish(
            exchange="micromail",
            routing_key=event_name,
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            )
        )
        
        connection.close()
        print(f"Published event: {event_name}")
    except Exception as e:
        print(f"Error publishing event: {str(e)}")


def extract_user_id(token: str) -> str:
    """Extract user ID from Authorization header token (simplified)"""
    # In a real implementation, this would verify the JWT token
    # For now, we'll extract from a custom header or use a mock
    return "user_123"


# ============ API Endpoints ============

@app.post("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "composer"}


@app.get("/drafts", response_model=DraftListResponse)
async def list_drafts(page: int = 1, limit: int = 20):
    """
    List all email drafts for the user
    """
    user_id = "user_123"  # Extract from token in real implementation
    
    # Filter drafts by user
    user_drafts = [d for d in drafts_db.values() if d["user_id"] == user_id]
    
    # Sort by creation date (newest first)
    user_drafts.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Pagination
    start = (page - 1) * limit
    end = start + limit
    paginated_drafts = user_drafts[start:end]
    
    return DraftListResponse(
        drafts=[DraftResponse(**d) for d in paginated_drafts],
        total=len(user_drafts),
        page=page,
        limit=limit
    )


@app.post("/drafts", response_model=DraftResponse)
async def create_draft(request: DraftCreate):
    """
    Create a new email draft
    """
    user_id = "user_123"  # Extract from token in real implementation
    
    # Create draft
    draft_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    draft_data = {
        "id": draft_id,
        "user_id": user_id,
        "to": request.to,
        "subject": request.subject,
        "body": request.body,
        "cc": request.cc,
        "bcc": request.bcc,
        "attachments": [{"id": str(uuid.uuid4()), "filename": a} for a in (request.attachments or [])],
        "created_at": now,
        "updated_at": now,
    }
    
    drafts_db[draft_id] = draft_data
    
    # Publish event
    publish_event("draft.created", {
        "draft_id": draft_id,
        "user_id": user_id,
        "timestamp": now
    })
    
    return DraftResponse(**draft_data)


@app.get("/drafts/{draft_id}", response_model=DraftResponse)
async def get_draft(draft_id: str):
    """
    Get a specific draft by ID
    """
    draft = drafts_db.get(draft_id)
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return DraftResponse(**draft)


@app.put("/drafts/{draft_id}", response_model=DraftResponse)
async def update_draft(draft_id: str, request: DraftUpdate):
    """
    Update an existing draft
    """
    draft = drafts_db.get(draft_id)
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Update fields
    now = datetime.now(timezone.utc).isoformat()
    
    if request.to is not None:
        draft["to"] = request.to
    if request.subject is not None:
        draft["subject"] = request.subject
    if request.body is not None:
        draft["body"] = request.body
    if request.cc is not None:
        draft["cc"] = request.cc
    if request.bcc is not None:
        draft["bcc"] = request.bcc
    
    draft["updated_at"] = now
    
    drafts_db[draft_id] = draft
    
    # Publish event
    publish_event("draft.updated", {
        "draft_id": draft_id,
        "timestamp": now
    })
    
    return DraftResponse(**draft)


@app.delete("/drafts/{draft_id}")
async def delete_draft(draft_id: str):
    """
    Delete a draft permanently
    """
    if draft_id not in drafts_db:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    del drafts_db[draft_id]
    
    # Publish event
    publish_event("draft.deleted", {
        "draft_id": draft_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"status": "ok", "message": "Draft deleted successfully"}


@app.post("/drafts/{draft_id}/send")
async def send_draft(draft_id: str):
    """
    Send a draft email
    
    Publishes email.send event to RabbitMQ for the delivery service to process
    """
    draft = drafts_db.get(draft_id)
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Create email from draft
    email_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    email_data = {
        "email_id": email_id,
        "user_id": draft["user_id"],
        "from": "user@micromail.com",  # Should come from user profile
        "to": draft["to"],
        "cc": draft.get("cc"),
        "bcc": draft.get("bcc"),
        "subject": draft["subject"],
        "body": draft["body"],
        "attachments": draft.get("attachments", []),
        "sent_at": now,
        "status": "pending"
    }
    
    # Publish email.send event to RabbitMQ
    # The delivery service will consume this event and send the email
    publish_event("email.send", email_data)
    
    # Delete draft after sending
    del drafts_db[draft_id]
    
    # Publish draft.sent event
    publish_event("draft.sent", {
        "draft_id": draft_id,
        "email_id": email_id,
        "timestamp": now
    })
    
    return {
        "status": "ok",
        "message": "Email sent successfully",
        "email_id": email_id
    }


@app.post("/attachments")
async def upload_attachment(attachment_id: str, filename: str):
    """
    Handle attachment upload (placeholder)
    
    In a real implementation, this would handle file uploads
    and store them in S3 or similar cloud storage
    """
    return {
        "attachment_id": attachment_id,
        "filename": filename,
        "size": 0,
        "mime_type": "application/octet-stream"
    }


@app.get("/attachments/{attachment_id}")
async def download_attachment(attachment_id: str):
    """
    Download an attachment (placeholder)
    """
    return {
        "attachment_id": attachment_id,
        "download_url": f"https://cdn.micromail.com/attachments/{attachment_id}"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
