from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
import httpx
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from middleware.auth import JWTBearer, verify_token, decode_token

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
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={"Access-Control-Allow-Origin": "*"},
    )
# JWT Bearer authentication
jwt_bearer = JWTBearer(auto_error=False)


def proxy_response(response: httpx.Response) -> JSONResponse:
    """Convert an httpx response to a JSONResponse, handling empty or non-JSON bodies."""
    try:
        content = response.json()
    except Exception:
        content = {"detail": response.text or "Upstream error"}
    return JSONResponse(status_code=response.status_code, content=content)


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
            return proxy_response(response)
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
            return proxy_response(response)
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
            return proxy_response(response)
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
            return proxy_response(response)
        except httpx.RequestError as e:
            logger.error(f"Auth Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth Service unavailable"
            )


# ==================== DRAFTS ROUTES ====================

@app.get("/api/drafts")
async def list_drafts(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(jwt_bearer)):
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
            return proxy_response(response)
        except httpx.RequestError as e:
            logger.error(f"Composer Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Composer Service unavailable"
            )


@app.post("/api/drafts")
async def create_draft(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(jwt_bearer)):
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
            return proxy_response(response)
        except httpx.RequestError as e:
            logger.error(f"Composer Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Composer Service unavailable"
            )


@app.put("/api/drafts/{draft_id}")
async def update_draft(draft_id: str, request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(jwt_bearer)):
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
            return proxy_response(response)
        except httpx.RequestError as e:
            logger.error(f"Composer Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Composer Service unavailable"
            )


@app.delete("/api/drafts/{draft_id}")
async def delete_draft(draft_id: str, request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(jwt_bearer)):
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
            return proxy_response(response)
        except httpx.RequestError as e:
            logger.error(f"Composer Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Composer Service unavailable"
            )


@app.post("/api/drafts/{draft_id}/send")
async def send_draft(draft_id: str, request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(jwt_bearer)):
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
            return proxy_response(response)
        except httpx.RequestError as e:
            logger.error(f"Composer Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Composer Service unavailable"
            )


# ==================== EMAIL ROUTES ====================

@app.get("/api/inbox")
async def get_inbox(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(jwt_bearer), skip: int = 0, limit: int = 50):
    """Get user's inbox emails - forward to Mail Service"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    token = credentials.credentials
    payload = decode_token(token)
    user_email = payload.get("email") if payload else None
    if not user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.MAIL_SERVICE_URL}/mails",
                params={"email": user_email, "box": "inbox", "skip": skip, "limit": limit},
                timeout=10.0
            )
            return proxy_response(response)
        except httpx.RequestError as e:
            logger.error(f"Mail Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Mail Service unavailable"
            )


@app.get("/api/sent")
async def get_sent(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(jwt_bearer), skip: int = 0, limit: int = 50):
    """Get user's sent emails - forward to Mail Service"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    token = credentials.credentials
    payload = decode_token(token)
    user_email = payload.get("email") if payload else None
    if not user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.MAIL_SERVICE_URL}/mails",
                params={"email": user_email, "box": "sent", "skip": skip, "limit": limit},
                timeout=10.0
            )
            return proxy_response(response)
        except httpx.RequestError as e:
            logger.error(f"Mail Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Mail Service unavailable"
            )


# ==================== MAIL ROUTES ====================

@app.get("/api/mails")
async def list_mails(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(jwt_bearer),
    box: str = "inbox",
    search: str = None,
    skip: int = 0,
    limit: int = 20
):
    """List mails by box - forward to Mail Service"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    token = credentials.credentials
    payload = decode_token(token)
    user_email = payload.get("email") if payload else None
    if not user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    params = {"email": user_email, "box": box, "skip": skip, "limit": limit}
    if search:
        params["search"] = search

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.MAIL_SERVICE_URL}/mails",
                params=params,
                timeout=10.0
            )
            return proxy_response(response)
        except httpx.RequestError as e:
            logger.error(f"Mail Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Mail Service unavailable"
            )


@app.post("/api/mails")
async def create_mail(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(jwt_bearer)):
    """Send a mail - forward to Mail Service with sender from JWT"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    token = credentials.credentials
    payload = decode_token(token)
    user_email = payload.get("email") if payload else None
    if not user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    body = await request.json()
    body["sender"] = user_email

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.MAIL_SERVICE_URL}/mails",
                json=body,
                timeout=10.0
            )
            return proxy_response(response)
        except httpx.RequestError as e:
            logger.error(f"Mail Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Mail Service unavailable"
            )


@app.get("/api/mails/{mail_id}")
async def get_mail(mail_id: int, request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(jwt_bearer)):
    """Get specific mail - forward to Mail Service"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.MAIL_SERVICE_URL}/mails/{mail_id}",
                timeout=10.0
            )
            return proxy_response(response)
        except httpx.RequestError as e:
            logger.error(f"Mail Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Mail Service unavailable"
            )


@app.delete("/api/mails/{mail_id}")
async def delete_mail(mail_id: int, request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(jwt_bearer)):
    """Delete mail - forward to Mail Service"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    token = credentials.credentials
    payload = decode_token(token)
    user_email = payload.get("email") if payload else None
    if not user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{settings.MAIL_SERVICE_URL}/mails/{mail_id}",
                params={"email": user_email},
                timeout=10.0
            )
            return proxy_response(response)
        except httpx.RequestError as e:
            logger.error(f"Mail Service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Mail Service unavailable"
            )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.API_GATEWAY_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
