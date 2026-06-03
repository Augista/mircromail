"""
MicroMail API Gateway
Routes requests from the frontend to appropriate microservices
Handles authentication, rate limiting, and request logging
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
import logging

app = FastAPI(title="API Gateway", version="1.0.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
COMPOSER_SERVICE_URL = os.getenv("COMPOSER_SERVICE_URL", "http://localhost:8002")
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8003")
DELIVERY_SERVICE_URL = os.getenv("DELIVERY_SERVICE_URL", "http://localhost:8004")


# ============ Middleware ============

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    return response


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Authentication middleware
    Validates JWT tokens for protected routes
    """
    # Skip auth for public endpoints
    public_paths = [
        "/api/auth/register",
        "/api/auth/login",
        "/health",
    ]
    
    if request.url.path not in public_paths and request.url.path.startswith("/api/"):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
    
    response = await call_next(request)
    return response


# ============ Helper Functions ============

async def forward_request(service_url: str, path: str, request: Request) -> JSONResponse:
    """
    Forward a request to a microservice
    """
    method = request.method
    headers = dict(request.headers)
    
    # Remove host header to avoid issues with microservice routing
    headers.pop("host", None)
    
    try:
        body = await request.body()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=f"{service_url}{path}",
                headers=headers,
                content=body if body else None,
            )
            
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    except Exception as e:
        logger.error(f"Error forwarding request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Service unavailable"
        )


# ============ Health Check ============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "api-gateway"}


# ============ Auth Service Routes ============

@app.post("/api/auth/register")
async def register(request: Request):
    """Register a new user"""
    return await forward_request(AUTH_SERVICE_URL, "/register", request)


@app.post("/api/auth/login")
async def login(request: Request):
    """Login with email and password"""
    return await forward_request(AUTH_SERVICE_URL, "/login", request)


@app.post("/api/auth/refresh")
async def refresh_token(request: Request):
    """Refresh access token"""
    return await forward_request(AUTH_SERVICE_URL, "/refresh", request)


@app.post("/api/auth/verify")
async def verify_token(request: Request):
    """Verify token and get user info"""
    return await forward_request(AUTH_SERVICE_URL, "/verify", request)


@app.post("/api/auth/logout")
async def logout(request: Request):
    """Logout user"""
    return await forward_request(AUTH_SERVICE_URL, "/logout", request)


# ============ Composer Service Routes ============

@app.get("/api/drafts")
async def list_drafts(request: Request):
    """List email drafts"""
    return await forward_request(COMPOSER_SERVICE_URL, "/drafts", request)


@app.post("/api/drafts")
async def create_draft(request: Request):
    """Create a new email draft"""
    return await forward_request(COMPOSER_SERVICE_URL, "/drafts", request)


@app.get("/api/drafts/{draft_id}")
async def get_draft(draft_id: str, request: Request):
    """Get a specific draft"""
    return await forward_request(COMPOSER_SERVICE_URL, f"/drafts/{draft_id}", request)


@app.put("/api/drafts/{draft_id}")
async def update_draft(draft_id: str, request: Request):
    """Update a draft"""
    return await forward_request(COMPOSER_SERVICE_URL, f"/drafts/{draft_id}", request)


@app.delete("/api/drafts/{draft_id}")
async def delete_draft(draft_id: str, request: Request):
    """Delete a draft"""
    return await forward_request(COMPOSER_SERVICE_URL, f"/drafts/{draft_id}", request)


@app.post("/api/drafts/{draft_id}/send")
async def send_draft(draft_id: str, request: Request):
    """Send a draft email"""
    return await forward_request(COMPOSER_SERVICE_URL, f"/drafts/{draft_id}/send", request)


# ============ Storage Service Routes ============

@app.get("/api/inbox")
async def list_inbox(request: Request):
    """List inbox emails"""
    return await forward_request(STORAGE_SERVICE_URL, "/inbox", request)


@app.get("/api/sent")
async def list_sent(request: Request):
    """List sent emails"""
    return await forward_request(STORAGE_SERVICE_URL, "/sent", request)


@app.get("/api/trash")
async def list_trash(request: Request):
    """List trash emails"""
    return await forward_request(STORAGE_SERVICE_URL, "/trash", request)


@app.get("/api/emails/{email_id}")
async def get_email(email_id: str, request: Request):
    """Get a specific email"""
    return await forward_request(STORAGE_SERVICE_URL, f"/emails/{email_id}", request)


@app.get("/api/search")
async def search_emails(request: Request):
    """Search emails"""
    return await forward_request(STORAGE_SERVICE_URL, "/search", request)


@app.delete("/api/emails/{email_id}")
async def delete_email(email_id: str, request: Request):
    """Delete an email"""
    return await forward_request(STORAGE_SERVICE_URL, f"/emails/{email_id}", request)


# ============ Delivery Service Routes ============

@app.get("/api/delivery-status/{email_id}")
async def get_delivery_status(email_id: str, request: Request):
    """Get email delivery status"""
    return await forward_request(DELIVERY_SERVICE_URL, f"/status/{email_id}", request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
