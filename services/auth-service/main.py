from fastapi import FastAPI, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from models import Base, User, RefreshToken
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

# Database setup
engine = create_engine(settings.AUTH_DB_URL, echo=settings.DEBUG)
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
        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=JWTManager.verify_token(refresh_token)['exp']
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
            expires_at=refresh_token_payload['exp']
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.AUTH_SERVICE_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
