"""
Authentication Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.models.database import get_db
from app.schemas.user_schemas import UserCreate, UserLogin, UserResponse, MFASetup, MFAVerify
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.utils.security import verify_token

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    user_service = UserService(db)
    
    # Check if user already exists
    if await user_service.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = await user_service.create_user(user_data)
    return user

@router.post("/login")
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Authenticate user and return tokens"""
    auth_service = AuthService(db)
    
    try:
        result = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password,
            ip_address=request.client.host
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/login/mfa")
async def login_with_mfa(
    mfa_data: MFAVerify,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Complete MFA authentication"""
    auth_service = AuthService(db)
    
    # This would require a temporary token from the initial login attempt
    # Implementation depends on your MFA flow design
    try:
        result = await auth_service.verify_mfa_and_complete_login(
            mfa_token=mfa_data.token,
            ip_address=request.client.host
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/refresh")
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Refresh access token using refresh token"""
    auth_service = AuthService(db)
    
    try:
        tokens = await auth_service.refresh_tokens(credentials.credentials)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Logout user and invalidate tokens"""
    auth_service = AuthService(db)
    
    try:
        await auth_service.logout_user(credentials.credentials)
        return {"message": "Successfully logged out"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        user_service = UserService(db)
        user = await user_service.get_user_by_id(int(user_id))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.post("/mfa/setup", response_model=MFASetup)
async def setup_mfa(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Setup MFA for user"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        auth_service = AuthService(db)
        mfa_setup = await auth_service.setup_mfa(int(user_id))
        
        return mfa_setup
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/mfa/verify")
async def verify_mfa_setup(
    mfa_data: MFAVerify,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Verify and enable MFA"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        auth_service = AuthService(db)
        result = await auth_service.verify_and_enable_mfa(
            user_id=int(user_id),
            token=mfa_data.token
        )
        
        return {"message": "MFA enabled successfully", "backup_codes": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/mfa/disable")
async def disable_mfa(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Disable MFA for user"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        auth_service = AuthService(db)
        await auth_service.disable_mfa(int(user_id))
        
        return {"message": "MFA disabled successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )