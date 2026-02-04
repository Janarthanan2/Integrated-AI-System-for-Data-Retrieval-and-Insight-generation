"""
Authentication service with JWT token management
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from ..db_models.user import User
from ..schemas.auth import UserCreate, UserLogin, Token, UserResponse

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours


class AuthService:
    """Service for handling authentication"""

    @staticmethod
    def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[str]:
        """Decode and verify JWT token, returns user_id"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except JWTError:
            return None

    @staticmethod
    async def register(db: AsyncSession, user_data: UserCreate) -> Token:
        """Register a new user"""
        # Check if email already exists
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        result = await db.execute(select(User).where(User.username == user_data.username))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        user = User(
            email=user_data.email,
            username=user_data.username
        )
        user.set_password(user_data.password)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Create access token
        access_token = AuthService.create_access_token(user.id)
        
        return Token(
            access_token=access_token,
            user=UserResponse.model_validate(user)
        )

    @staticmethod
    async def login(db: AsyncSession, login_data: UserLogin) -> Token:
        """Login user and return token"""
        # Find user by email
        result = await db.execute(select(User).where(User.email == login_data.email))
        user = result.scalar_one_or_none()
        
        if not user or not user.verify_password(login_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create access token
        access_token = AuthService.create_access_token(user.id)
        
        return Token(
            access_token=access_token,
            user=UserResponse.model_validate(user)
        )

    @staticmethod
    async def get_current_user(db: AsyncSession, token: str) -> User:
        """Get current user from token"""
        user_id = AuthService.decode_token(token)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
