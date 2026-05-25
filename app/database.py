import os
from sqlalchemy import create_engine, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column, DeclarativeBase, relationship
from datetime import datetime
from typing import Optional, List

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/vocaltolocal")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# ==================== UPDATED DATABASE TABLES ====================

class Area(Base):
    """Stores operating areas/locations (e.g., specific neighborhoods or pincodes)"""
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    area_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), default="Mumbai")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="area")
    businesses: Mapped[List["Business"]] = relationship(back_populates="area")


class User(Base):
    """Stores system users (Customers and Vendor Owners)"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="customer") # 'customer' or 'vendor'
    
    # Location linking
    area_id: Mapped[Optional[int]] = mapped_column(ForeignKey("areas.id"), nullable=True)
    area: Mapped[Optional["Area"]] = relationship(back_populates="users")
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Business(Base):
    """Stores local vendors registered under an Area"""
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(Integer, index=True) 
    business_name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True) 
    detailed_address: Mapped[str] = mapped_column(String(255))
    
    # Location linking
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"), nullable=False)
    area: Mapped["Area"] = relationship(back_populates="businesses")
    
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
