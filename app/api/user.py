from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.entities import get_async_session
from app.database.entities import userProfiles
from app.services.user_service import (
    UserCreate, UserResponse, Token,
    register_user, login_user, get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Register a new user.
    
    - **username**: Unique username
    - **email**: Unique email address
    - **password**: User password (will be hashed)
    """
    user = await register_user(db, user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Login with email (as username) and password.
    Returns JWT access token.
    
    - **username**: User's email address
    - **password**: User's password
    """
    token = await login_user(db, form_data.username, form_data.password)
    return token


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: userProfiles = Depends(get_current_user)):
    """
    Get current authenticated user information.
    Requires valid JWT token in Authorization header.
    """
    return current_user


@router.post("/logout")
async def logout(current_user: userProfiles = Depends(get_current_user)):
    """
    Logout endpoint (token invalidation should be handled client-side).
    This endpoint verifies the user is authenticated.
    """
    return {"message": "Successfully logged out"}


