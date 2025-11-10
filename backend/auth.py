"""
Authentication and authorization module
Handles JWT tokens, password hashing, and user verification
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import secrets

from backend.database import get_db, User, Tenant

# Security configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a unique API key"""
    return f"sk_{secrets.token_urlsafe(32)}"


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_by_api_key(db: Session, api_key: str) -> Optional[User]:
    """Get user by API key"""
    return db.query(User).filter(User.api_key == api_key).first()


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current authenticated user from token or API key
    Returns None if no authentication provided (for optional auth)
    """
    # Try API key first
    if x_api_key:
        user = get_user_by_api_key(db, x_api_key)
        if user and user.is_active:
            return user

    # Try JWT token
    if token:
        payload = decode_token(token)
        if payload:
            username: str = payload.get("sub")
            if username:
                user = db.query(User).filter(User.username == username).first()
                if user and user.is_active:
                    return user

    return None


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user (required authentication)
    Raises 401 if not authenticated
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Get the current admin user (required admin role)
    Raises 403 if not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_user_tenant(db: Session, user: User) -> Optional[Tenant]:
    """Get the default tenant for a user"""
    tenant = db.query(Tenant).filter(Tenant.owner_id == user.id).first()
    if not tenant:
        # Create default tenant for user
        tenant = Tenant(
            name=f"{user.username}'s Workspace",
            slug=f"{user.username}_workspace",
            owner_id=user.id,
            storage_path=f"./data/tenants/{user.id}"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    is_admin: bool = False
) -> User:
    """Create a new user"""
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        raise ValueError("User with this username or email already exists")

    # Create user
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        is_admin=is_admin,
        api_key=generate_api_key()
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create default tenant
    get_user_tenant(db, user)

    return user


def init_admin_user(db: Session):
    """Initialize default admin user if none exists"""
    admin = db.query(User).filter(User.is_admin == True).first()
    if not admin:
        try:
            admin = create_user(
                db=db,
                username="admin",
                email="admin@example.com",
                password="admin123",  # Change in production!
                full_name="Administrator",
                is_admin=True
            )
            print(f"✅ Created default admin user: username='admin', password='admin123'")
            print(f"   API Key: {admin.api_key}")
            print("⚠️  Please change the admin password immediately!")
        except ValueError:
            pass
