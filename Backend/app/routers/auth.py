"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..db_models.base import get_db
from ..schemas.auth import UserCreate, UserLogin, Token, UserResponse
from ..services.auth_service import AuthService
from ..activity_logger import get_logger

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    return await AuthService.get_current_user(db, token)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    - **email**: Valid email address (unique)
    - **username**: Username (3-100 chars, unique)
    - **password**: Password (min 6 chars)
    
    Returns JWT token on success.
    """
    result = await AuthService.register(db, user_data)

    # Log the registration as first login
    try:
        get_logger().log_login(result.user.id, result.user.username, result.user.email)
    except Exception as e:
        print(f"[ActivityLogger] Warning: Could not log registration: {e}")

    return result


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    
    Returns JWT token on success.
    """
    result = await AuthService.login(db, login_data)

    # Log the login event
    try:
        get_logger().log_login(result.user.id, result.user.username, result.user.email)
    except Exception as e:
        print(f"[ActivityLogger] Warning: Could not log login: {e}")

    return result


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user = Depends(get_current_user)
):
    """
    Get current authenticated user.
    
    Requires Bearer token in Authorization header.
    """
    return UserResponse.model_validate(current_user)


@router.post("/verify")
async def verify_token(
    current_user = Depends(get_current_user)
):
    """
    Verify if the current token is valid.
    
    Returns user info if valid.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email
    }
