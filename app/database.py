import os
from sqlalchemy import create_engine, String, Integer, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column, DeclarativeBase
from datetime import datetime
from typing import Optional

# 1. Fetch the Internal Database URL from Render Environment Settings
# If running locally, it defaults to a local PostgreSQL layout
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/vocaltolocal")

# Fix for Render/PostgreSQL connection strings using old 'postgres://' format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Create Database Engine and Session Factory
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Create Modern Declarative Base for Tables
class Base(DeclarativeBase):
    pass

# ==================== DATABASE TABLES (MODELS) ====================

class User(Base):
    """Stores information about system users/customers"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Business(Base):
    """Stores local vendors/shops registered under Vocal to Local"""
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(Integer, index=True) # Connects to User.id later
    business_name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True) # e.g., Grocery, Dairy, Clothes
    address: Mapped[str] = mapped_column(String(255))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# 4. Dependency function to easily yield database sessions to API routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
