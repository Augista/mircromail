from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from middleware.auth import JWTBearer, verify_token

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MicroMail API Gateway",
    description="Central routing gateway for all microservices",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Bearer authentication
jwt_bearer = JWTBearer(auto_error=False)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "API Gateway"
    }


# ==================== AUTH ROUTES ====================

@app.post("/api/auth/register")
async def register(request: Request):
    """Register new user - forward to Auth Service"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/register",
                json=body,
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Auth Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth Service unavailable"
            )


@app.post("/api/auth/login")
async def login(request: Request):
    """Login user - forward to Auth Service"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/login",
                json=body,
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Auth Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth Service unavailable"
            )


@app.get("/api/auth/me")
async def get_current_user(request: Request):
    """Forward current user profile request to Auth Service"""
    auth_header = request.headers.get('authorization')
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing authorization header')

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/me",
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Auth Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth Service unavailable"
            )


@app.post("/api/auth/refresh")
async def refresh(request: Request):
    """Refresh JWT token - forward to Auth Service"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/refresh",
                json=body,
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Auth Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth Service unavailable"
            )


# ==================== DRAFTS ROUTES ====================

@app.get("/api/drafts")
async def list_drafts(request: Request, credentials = jwt_bearer):
    """List user's drafts"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.COMPOSER_SERVICE_URL}/drafts",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Composer Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Composer Service unavailable"
            )


@app.post("/api/drafts")
async def create_draft(request: Request, credentials = jwt_bearer):
    """Create new draft"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    token = credentials.credentials
    body = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.COMPOSER_SERVICE_URL}/drafts",
                json=body,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Composer Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Composer Service unavailable"
            )


@app.put("/api/drafts/{draft_id}")
async def update_draft(draft_id: str, request: Request, credentials = jwt_bearer):
    """Update draft"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    token = credentials.credentials
    body = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{settings.COMPOSER_SERVICE_URL}/drafts/{draft_id}",
                json=body,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Composer Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Composer Service unavailable"
            )


@app.delete("/api/drafts/{draft_id}")
async def delete_draft(draft_id: str, request: Request, credentials = jwt_bearer):
    """Delete draft"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{settings.COMPOSER_SERVICE_URL}/drafts/{draft_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Composer Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Composer Service unavailable"
            )


@app.post("/api/drafts/{draft_id}/send")
async def send_draft(draft_id: str, request: Request, credentials = jwt_bearer):
    """Send draft (publishes email.send event)"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.COMPOSER_SERVICE_URL}/drafts/{draft_id}/send",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Composer Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Composer Service unavailable"
            )


# ==================== EMAIL ROUTES ====================

@app.get("/api/inbox")
async def get_inbox(request: Request, credentials = jwt_bearer, skip: int = 0, limit: int = 50):
    """Get user's inbox emails"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.STORAGE_SERVICE_URL}/emails/inbox",
                headers={"Authorization": f"Bearer {token}"},
                params={"skip": skip, "limit": limit},
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Storage Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Storage Service unavailable"
            )


@app.get("/api/sent")
async def get_sent(request: Request, credentials = jwt_bearer, skip: int = 0, limit: int = 50):
    """Get user's sent emails"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.STORAGE_SERVICE_URL}/emails/sent",
                headers={"Authorization": f"Bearer {token}"},
                params={"skip": skip, "limit": limit},
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Storage Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Storage Service unavailable"
            )


@app.get("/api/emails/{email_id}")
async def get_email(email_id: str, request: Request, credentials = jwt_bearer):
    """Get email details"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.STORAGE_SERVICE_URL}/emails/{email_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Storage Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Storage Service unavailable"
            )


@app.get("/api/emails/search")
async def search_emails(request: Request, credentials = jwt_bearer, query: str = ""):
    """Search emails"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.STORAGE_SERVICE_URL}/emails/search",
                headers={"Authorization": f"Bearer {token}"},
                params={"query": query},
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Storage Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Storage Service unavailable"
            )


@app.post("/api/emails/{email_id}/mark-read")
async def mark_email_read(email_id: str, request: Request, credentials = jwt_bearer):
    """Mark email as read"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    token = credentials.credentials
    body = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.STORAGE_SERVICE_URL}/emails/{email_id}/mark-read",
                json=body,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Storage Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Storage Service unavailable"
            )


@app.delete("/api/emails/{email_id}")
async def delete_email(email_id: str, request: Request, credentials = jwt_bearer):
    """Delete/archive email"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{settings.STORAGE_SERVICE_URL}/emails/{email_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        except httpx.RequestError as e:
            logger.error(f"Storage Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Storage Service unavailable"
            )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.API_GATEWAY_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
