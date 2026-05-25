import os
from sqlalchemy import create_engine, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, DeclarativeBase, relationship
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
    
    # Matches buyer.html frontend payload address data strings
    detailed_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

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
    detailed_address: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # GST Identification Number (Optional for micro-vendors)
    gst_number: Mapped[Optional[str]] = mapped_column(String(15), nullable=True, index=True)
    
    # Subscription status tracking for monetization management
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Location linking
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"), nullable=False)
    area: Mapped["Area"] = relationship(back_populates="businesses")
    
    # ✅ FIXED: Added relationship mapper back so main.py catalog tools work smoothly
    products: Mapped[List["Product"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Product(Base):
    """Stores Sunday-Friday Daily Discovery Digital Catalog Items"""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # ✅ FIXED: Adjusted from Integer to Float type to hold standard price formats
    regular_price: Mapped[float] = mapped_column(Float, nullable=False) 
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    
    business: Mapped["Business"] = relationship(back_populates="products")

class AuctionRequest(Base):
    """Stores the weekly shopping lists dropped by buyers for the Saturday auction"""
    __tablename__ = "auction_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    buyer_id: Mapped[int] = mapped_column(Integer, index=True)
    items_list: Mapped[str] = mapped_column(String(500), nullable=False) # e.g., "5kg Rice, 2L Oil"
    target_pincode: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    max_budget: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open") # open, closed, expired
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship link to counter-bids
    bids: Mapped[List["AuctionBid"]] = relationship(back_populates="auction", cascade="all, delete-orphan")


class AuctionBid(Base):
    """Stores real-time reverse-bids placed by local merchants to win orders"""
    __tablename__ = "auction_bids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    auction_id: Mapped[int] = mapped_column(ForeignKey("auction_requests.id"), nullable=False)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False)
    bid_amount: Mapped[float] = mapped_column(Float, nullable=False) # The downward-competing offer
    delivery_time: Mapped[str] = mapped_column(String(50), default="Immediate") 
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    auction: Mapped["AuctionRequest"] = relationship(back_populates="bids")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
