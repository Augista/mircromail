from fastapi import FastAPI, HTTPException, Request, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import logging
import sys
import os
from uuid import UUID
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone



# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from models import User, RefreshToken
from schemas import (
    UserRegister, UserLogin, RefreshTokenRequest,
    AuthResponse, UserResponse, TokenResponse
)
from utils import PasswordManager, JWTManager

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MicroMail Auth Service",
    description="User authentication and JWT token management",
    version="1.0.0"
)

origins = [  "http://localhost",
    "http://localhost:3000",]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
engine = create_engine(settings.AUTH_DB_URL, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Auth Service"
    }


@app.post("/register", response_model=AuthResponse)
async def register(request: UserRegister):
    """Register new user"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = PasswordManager.hash_password(request.password)
        
        # Create user
        user = User(
            email=request.email,
            name=request.name,
            password_hash=password_hash
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Generate tokens
        access_token = JWTManager.create_access_token(str(user.id), user.email)
        refresh_token = JWTManager.create_refresh_token(str(user.id), user.email)
        
        # Store refresh token
        refresh_token_payload = JWTManager.verify_token(refresh_token)
        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.fromtimestamp(refresh_token_payload['exp'], tz=timezone.utc)
        )
        db.add(refresh_token_obj)
        db.commit()
        
        logger.info(f"User registered: {user.email}")
        
        return AuthResponse(
            user=UserResponse.from_orm(user),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=JWTManager.get_token_expiration_seconds('access')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )
    finally:
        db.close()


@app.post("/login", response_model=AuthResponse)
async def login(request: UserLogin):
    """Login user"""
    db = SessionLocal()
    try:
        # Find user
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not PasswordManager.verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate tokens
        access_token = JWTManager.create_access_token(str(user.id), user.email)
        refresh_token = JWTManager.create_refresh_token(str(user.id), user.email)
        
        # Store refresh token
        refresh_token_payload = JWTManager.verify_token(refresh_token)
        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.fromtimestamp(refresh_token_payload['exp'], tz=timezone.utc)
        )
        db.add(refresh_token_obj)
        db.commit()
        
        logger.info(f"User logged in: {user.email}")
        
        return AuthResponse(
            user=UserResponse.from_orm(user),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=JWTManager.get_token_expiration_seconds('access')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )
    finally:
        db.close()


@app.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(request: RefreshTokenRequest):
    """Refresh access token"""
    db = SessionLocal()
    try:
        # Verify refresh token
        payload = JWTManager.verify_token(request.refresh_token)
        if not payload or payload.get('type') != 'refresh':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if token exists in database
        token_obj = db.query(RefreshToken).filter(
            RefreshToken.token == request.refresh_token
        ).first()
        if not token_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked"
            )
        
        # Get user
        user = token_obj.user
        
        # Create new access token
        access_token = JWTManager.create_access_token(str(user.id), user.email)
        
        logger.info(f"Token refreshed for user: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=request.refresh_token,
            expires_in=JWTManager.get_token_expiration_seconds('access')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )
    finally:
        db.close()


@app.get('/me', response_model=UserResponse)
async def get_current_user(request: Request):
    """Get current authenticated user"""
    db = SessionLocal()
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Missing or invalid authorization header'
            )

        token = auth_header.split(' ', 1)[1]
        payload = JWTManager.verify_token(token)
        if not payload or payload.get('type') != 'access':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid or expired access token'
            )

        user_id = payload.get('sub')
        try:
            user_id = UUID(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid token subject'
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )

        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to load current user'
        )
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.AUTH_SERVICE_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
