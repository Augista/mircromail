"""
MicroMail Auth Service
Handles user authentication, registration, and token management
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
import os
import jwt
from passlib.context import CryptContext
import uuid

app = FastAPI(title="Auth Service", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mock database - will be replaced with PostgreSQL
users_db: dict = {}
tokens_db: dict = {}


# ============ Request/Response Models ============

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: str


# ============ Helper Functions ============

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============ API Endpoints ============

@app.post("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "auth"}


@app.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """
    Register a new user
    
    Returns access and refresh tokens on success
    """
    # Check if user already exists
    if any(u["email"] == request.email for u in users_db.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "name": request.name,
        "email": request.email,
        "password_hash": hash_password(request.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    users_db[user_id] = user_data
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(
        data={"sub": user_id, "type": "access"},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_token(
        data={"sub": user_id, "type": "refresh"},
        expires_delta=timedelta(days=7)
    )
    
    # Store refresh token
    tokens_db[user_id] = {
        "refresh_token": refresh_token,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login with email and password
    
    Returns access and refresh tokens on success
    """
    # Find user by email
    user = next((u for u in users_db.values() if u["email"] == request.email), None)
    
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(
        data={"sub": user["id"], "type": "access"},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_token(
        data={"sub": user["id"], "type": "refresh"},
        expires_delta=timedelta(days=7)
    )
    
    # Store refresh token
    tokens_db[user["id"]] = {
        "refresh_token": refresh_token,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token
    """
    payload = verify_token(refresh_token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user_id = payload.get("sub")
    
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(
        data={"sub": user_id, "type": "access"},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.post("/verify")
async def verify(token: str) -> UserResponse:
    """
    Verify token and return user information
    """
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"]
    )


@app.post("/logout")
async def logout(token: str):
    """
    Logout user and invalidate tokens
    """
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    # Remove refresh token
    if user_id in tokens_db:
        del tokens_db[user_id]
    
    return {"status": "ok", "message": "Successfully logged out"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
