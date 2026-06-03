from fastapi import FastAPI, HTTPException, status, Depends, Header
from sqlalchemy import create_engine, or_, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import text
import jwt
import logging
import sys
import os
from uuid import UUID
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from models import Base, Email
from schemas import (
    EmailResponse, EmailListResponse, EmailDetailResponse,
    MarkReadRequest, SearchResponse
)

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MicroMail Storage Service",
    description="Email storage and retrieval with CQRS pattern",
    version="1.0.0"
)

# Database setup
engine = create_engine(settings.STORAGE_DB_URL, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_token(authorization: str = Header(None)) -> dict:
    """Verify JWT token from Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Storage Service"
    }


@app.get("/emails/inbox", response_model=EmailListResponse)
async def get_inbox(
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
    skip: int = 0,
    limit: int = 50
):
    """Get inbox emails for authenticated user"""
    user_id = UUID(token_payload.get("sub"))
    
    # Get total count
    total = db.query(Email).filter(
        Email.user_id == user_id,
        Email.folder == 'inbox'
    ).count()
    
    # Get paginated emails
    emails = db.query(Email).filter(
        Email.user_id == user_id,
        Email.folder == 'inbox'
    ).order_by(
        desc(Email.timestamp)
    ).offset(skip).limit(limit).all()
    
    logger.info(f"Retrieved {len(emails)} inbox emails for user: {user_id}")
    
    return EmailListResponse(
        total=total,
        skip=skip,
        limit=limit,
        emails=[EmailResponse.from_orm(e) for e in emails]
    )


@app.get("/emails/sent", response_model=EmailListResponse)
async def get_sent(
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
    skip: int = 0,
    limit: int = 50
):
    """Get sent emails for authenticated user"""
    user_id = UUID(token_payload.get("sub"))
    
    # Get total count
    total = db.query(Email).filter(
        Email.user_id == user_id,
        Email.folder == 'sent'
    ).count()
    
    # Get paginated emails
    emails = db.query(Email).filter(
        Email.user_id == user_id,
        Email.folder == 'sent'
    ).order_by(
        desc(Email.timestamp)
    ).offset(skip).limit(limit).all()
    
    logger.info(f"Retrieved {len(emails)} sent emails for user: {user_id}")
    
    return EmailListResponse(
        total=total,
        skip=skip,
        limit=limit,
        emails=[EmailResponse.from_orm(e) for e in emails]
    )


@app.get("/emails/{email_id}", response_model=EmailDetailResponse)
async def get_email(
    email_id: str,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    """Get email by ID"""
    user_id = UUID(token_payload.get("sub"))
    email_uuid = UUID(email_id)
    
    email = db.query(Email).filter(
        Email.id == email_uuid,
        Email.user_id == user_id
    ).first()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    # Mark as read if not already
    if not email.is_read:
        email.is_read = True
        db.commit()
    
    return EmailDetailResponse.from_orm(email)


@app.get("/emails/search", response_model=SearchResponse)
async def search_emails(
    query: str,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
    skip: int = 0,
    limit: int = 50
):
    """Search emails by subject and body"""
    user_id = UUID(token_payload.get("sub"))
    
    # Full-text search using PostgreSQL tsvector
    search_vector = text("""
        to_tsvector('english', subject || ' ' || COALESCE(body, ''))
        @@ plainto_tsquery('english', :query)
    """)
    
    # Get total count
    total = db.query(Email).filter(
        Email.user_id == user_id,
        search_vector
    ).params(query=query).count()
    
    # Get paginated results
    results = db.query(Email).filter(
        Email.user_id == user_id,
        search_vector
    ).params(query=query).order_by(
        desc(Email.timestamp)
    ).offset(skip).limit(limit).all()
    
    logger.info(f"Search returned {len(results)} results for query: {query}, user: {user_id}")
    
    return SearchResponse(
        total=total,
        query=query,
        results=[EmailResponse.from_orm(e) for e in results]
    )


@app.post("/emails/{email_id}/mark-read", response_model=EmailResponse)
async def mark_email_read(
    email_id: str,
    request: MarkReadRequest,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    """Mark email as read/unread"""
    user_id = UUID(token_payload.get("sub"))
    email_uuid = UUID(email_id)
    
    email = db.query(Email).filter(
        Email.id == email_uuid,
        Email.user_id == user_id
    ).first()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    email.is_read = request.is_read
    db.commit()
    db.refresh(email)
    
    logger.info(f"Marked email {email_uuid} as read: {request.is_read}")
    
    return EmailResponse.from_orm(email)


@app.delete("/emails/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email(
    email_id: str,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    """Delete/archive email"""
    user_id = UUID(token_payload.get("sub"))
    email_uuid = UUID(email_id)
    
    email = db.query(Email).filter(
        Email.id == email_uuid,
        Email.user_id == user_id
    ).first()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    # Move to trash instead of hard delete
    email.folder = 'trash'
    db.commit()
    
    logger.info(f"Moved email {email_uuid} to trash")


# RabbitMQ Event Listener (for storing incoming emails)
def start_event_listener():
    """Start listening for email.delivered events"""
    import pika
    import json
    
    try:
        connection = pika.BlockingConnection(
            pika.URLParameters(settings.RABBITMQ_URL)
        )
        channel = connection.channel()
        
        # Declare exchange and queue
        channel.exchange_declare(
            exchange='micromail-events',
            exchange_type='topic',
            durable=True
        )
        
        channel.queue_declare(
            queue='storage-service-queue',
            durable=True
        )
        
        channel.queue_bind(
            exchange='micromail-events',
            queue='storage-service-queue',
            routing_key='email.delivered'
        )
        
        def callback(ch, method, properties, body):
            try:
                db = SessionLocal()
                event = json.loads(body)
                
                # Store email in database
                email = Email(
                    user_id=UUID(event['user_id']),
                    from_email=event['data'].get('from_email', ''),
                    from_name=event['data'].get('from_name'),
                    to_email=event['data'].get('to_email', ''),
                    cc=event['data'].get('cc'),
                    bcc=event['data'].get('bcc'),
                    subject=event['data'].get('subject', ''),
                    body=event['data'].get('body'),
                    preview=event['data'].get('body', '')[:500],
                    folder='inbox',
                    timestamp=datetime.fromisoformat(event['data'].get('timestamp', datetime.utcnow().isoformat()))
                )
                
                db.add(email)
                db.commit()
                logger.info(f"Stored email {email.id} in storage")
                
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing email.delivered event: {str(e)}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            finally:
                db.close()
        
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue='storage-service-queue',
            on_message_callback=callback
        )
        
        logger.info("Started listening for email.delivered events")
        channel.start_consuming()
    except Exception as e:
        logger.error(f"RabbitMQ listener error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    import threading
    
    # Start RabbitMQ listener in background
    listener_thread = threading.Thread(target=start_event_listener, daemon=True)
    listener_thread.start()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.STORAGE_SERVICE_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
