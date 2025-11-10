"""
Authentication and user management API routes
"""
from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from backend.database import get_db, User, Tenant, UploadedFile, QueryHistory
from backend.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_admin_user,
    create_user,
    get_password_hash,
    generate_api_key,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    api_key: Optional[str] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class TenantResponse(BaseModel):
    id: int
    name: str
    slug: str
    owner_id: int

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    total_files: int
    total_queries: int
    storage_used: str


# Routes
@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        user = create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    if user_update.full_name:
        current_user.full_name = user_update.full_name
    if user_update.email:
        current_user.email = user_update.email
    if user_update.password:
        current_user.hashed_password = get_password_hash(user_update.password)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/regenerate-api-key", response_model=UserResponse)
async def regenerate_api_key(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Regenerate API key for current user"""
    current_user.api_key = generate_api_key()
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get statistics for current user"""
    total_files = db.query(UploadedFile).filter(UploadedFile.user_id == current_user.id).count()
    total_queries = db.query(QueryHistory).filter(QueryHistory.user_id == current_user.id).count()

    # Calculate storage used
    files = db.query(UploadedFile).filter(UploadedFile.user_id == current_user.id).all()
    storage_bytes = sum(f.file_size or 0 for f in files)
    storage_mb = storage_bytes / (1024 * 1024)

    return {
        "total_files": total_files,
        "total_queries": total_queries,
        "storage_used": f"{storage_mb:.2f} MB"
    }


@router.get("/me/tenants", response_model=List[TenantResponse])
async def get_user_tenants(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get tenants for current user"""
    tenants = db.query(Tenant).filter(Tenant.owner_id == current_user.id).all()
    return tenants


# Admin routes
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all users (admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.post("/users", response_model=UserResponse)
async def create_user_admin(
    user_data: UserCreate,
    is_admin: bool = False,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    try:
        user = create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            is_admin=is_admin
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_admin and user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    db.delete(user)
    db.commit()

    return {"success": True, "message": f"User {user.username} deleted"}


@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Toggle user active status (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    return {"success": True, "is_active": user.is_active}
