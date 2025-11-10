"""
Database models and connection for user management and multi-tenancy
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database URL - uses SQLite for simplicity, can be changed to PostgreSQL/MySQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # API Key for programmatic access
    api_key = Column(String(100), unique=True, index=True)

    # Relationships
    tenants = relationship("Tenant", back_populates="owner")
    uploaded_files = relationship("UploadedFile", back_populates="user")


class Tenant(Base):
    """Tenant model for multi-tenancy - isolates data per user/organization"""
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Storage path for this tenant's data
    storage_path = Column(String(255))

    # Relationships
    owner = relationship("User", back_populates="tenants")
    uploaded_files = relationship("UploadedFile", back_populates="tenant")


class UploadedFile(Base):
    """Track uploaded files per user/tenant"""
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))

    # User and Tenant association
    user_id = Column(Integer, ForeignKey("users.id"))
    tenant_id = Column(Integer, ForeignKey("tenants.id"))

    # Metadata
    rows_count = Column(Integer)
    columns_count = Column(Integer)
    chunks_created = Column(Integer)
    upload_date = Column(DateTime, default=datetime.utcnow)

    # Status
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)

    # Relationships
    user = relationship("User", back_populates="uploaded_files")
    tenant = relationship("Tenant", back_populates="uploaded_files")


class QueryHistory(Base):
    """Track user queries for analytics"""
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text)
    execution_time = Column(Integer)  # milliseconds
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    """Dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


if __name__ == "__main__":
    init_db()
