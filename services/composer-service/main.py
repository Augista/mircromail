from fastapi import FastAPI, HTTPException, status, Depends, Header
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import jwt
import logging
import sys
import os
from uuid import UUID, uuid4
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from models import Base, Draft, Attachment
from schemas import (
    DraftCreate, DraftUpdate, DraftResponse, DraftListResponse,
    SendDraftRequest, DraftSentResponse
)
from rabbitmq import get_publisher

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MicroMail Composer Service",
    description="Draft email management and composition",
    version="1.0.0"
)

# Database setup
engine = create_engine(settings.COMPOSER_DB_URL, echo=settings.DEBUG)
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
        "service": "Composer Service"
    }


@app.get("/drafts", response_model=DraftListResponse)
async def list_drafts(
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token),
    skip: int = 0,
    limit: int = 50
):
    """List all drafts for authenticated user"""
    user_id = UUID(token_payload.get("sub"))
    
    # Get total count
    total = db.query(Draft).filter(Draft.user_id == user_id).count()
    
    # Get paginated drafts
    drafts = db.query(Draft).filter(
        Draft.user_id == user_id
    ).order_by(
        Draft.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    logger.info(f"Listed {len(drafts)} drafts for user: {user_id}")
    
    return DraftListResponse(
        total=total,
        skip=skip,
        limit=limit,
        drafts=[DraftResponse.from_orm(d) for d in drafts]
    )


@app.post("/drafts", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
async def create_draft(
    request: DraftCreate,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    """Create new draft"""
    user_id = UUID(token_payload.get("sub"))
    
    draft = Draft(
        user_id=user_id,
        to_email=request.to_email,
        cc=request.cc,
        bcc=request.bcc,
        subject=request.subject,
        body=request.body
    )
    
    db.add(draft)
    db.commit()
    db.refresh(draft)
    
    # Publish draft.created event
    try:
        publisher = get_publisher()
        publisher.publish_event(
            event_type="draft.created",
            user_id=str(user_id),
            data={
                "draft_id": str(draft.id),
                "to_email": draft.to_email,
                "subject": draft.subject
            }
        )
    except Exception as e:
        logger.warning(f"Failed to publish draft.created event: {str(e)}")
    
    logger.info(f"Created draft {draft.id} for user {user_id}")
    return DraftResponse.from_orm(draft)


@app.get("/drafts/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    """Get draft by ID"""
    user_id = UUID(token_payload.get("sub"))
    draft_uuid = UUID(draft_id)
    
    draft = db.query(Draft).filter(
        Draft.id == draft_uuid,
        Draft.user_id == user_id
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    return DraftResponse.from_orm(draft)


@app.put("/drafts/{draft_id}", response_model=DraftResponse)
async def update_draft(
    draft_id: str,
    request: DraftUpdate,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    """Update draft"""
    user_id = UUID(token_payload.get("sub"))
    draft_uuid = UUID(draft_id)
    
    draft = db.query(Draft).filter(
        Draft.id == draft_uuid,
        Draft.user_id == user_id
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    # Update fields if provided
    if request.to_email is not None:
        draft.to_email = request.to_email
    if request.cc is not None:
        draft.cc = request.cc
    if request.bcc is not None:
        draft.bcc = request.bcc
    if request.subject is not None:
        draft.subject = request.subject
    if request.body is not None:
        draft.body = request.body
    
    draft.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(draft)
    
    # Publish draft.updated event
    try:
        publisher = get_publisher()
        publisher.publish_event(
            event_type="draft.updated",
            user_id=str(user_id),
            data={
                "draft_id": str(draft.id),
                "to_email": draft.to_email,
                "subject": draft.subject
            }
        )
    except Exception as e:
        logger.warning(f"Failed to publish draft.updated event: {str(e)}")
    
    logger.info(f"Updated draft {draft.id} for user {user_id}")
    return DraftResponse.from_orm(draft)


@app.delete("/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    """Delete draft"""
    user_id = UUID(token_payload.get("sub"))
    draft_uuid = UUID(draft_id)
    
    draft = db.query(Draft).filter(
        Draft.id == draft_uuid,
        Draft.user_id == user_id
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    db.delete(draft)
    db.commit()
    
    logger.info(f"Deleted draft {draft.id} for user {user_id}")


@app.post("/drafts/{draft_id}/send", response_model=DraftSentResponse)
async def send_draft(
    draft_id: str,
    request: SendDraftRequest,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    """Send draft (publish email.send event)"""
    user_id = UUID(token_payload.get("sub"))
    draft_uuid = UUID(draft_id)
    
    draft = db.query(Draft).filter(
        Draft.id == draft_uuid,
        Draft.user_id == user_id
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    # Validate email has required fields
    if not draft.to_email or not draft.subject or not draft.body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Draft must have to_email, subject, and body"
        )
    
    # Generate event ID
    event_id = uuid4()
    
    # Publish email.send event to Delivery Service
    try:
        publisher = get_publisher()
        publisher.publish_event(
            event_type="email.send",
            user_id=str(user_id),
            data={
                "draft_id": str(draft.id),
                "event_id": str(event_id),
                "from_email": token_payload.get("email"),
                "to_email": draft.to_email,
                "cc": draft.cc,
                "bcc": draft.bcc,
                "subject": draft.subject,
                "body": draft.body,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        logger.info(f"Published email.send event for draft {draft.id}")
    except Exception as e:
        logger.error(f"Failed to publish email.send event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )
    
    return DraftSentResponse(
        success=True,
        message="Email queued for delivery",
        draft_id=draft.id,
        event_id=event_id
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.COMPOSER_SERVICE_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
