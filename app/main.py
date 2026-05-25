import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import engine, Base, get_db, Area, User, Business

# ✅ FIXED: Commented out to prevent the SQLAlchemy metadata conflict crash
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vocal to Local API")

# ==================== PYDANTIC VALIDATION SCHEMAS ====================
class AreaCreate(BaseModel):
    area_name: str
    pincode: str
    city: str

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str
    role: str = "customer"
    area_id: Optional[int] = None

class BusinessCreate(BaseModel):
    owner_id: int
    business_name: str
    category: str
    detailed_address: str
    area_id: int

# Combined payload handling maps manual frontend details directly
class VendorOnboardPayload(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str
    business_name: str
    category: str
    gst_number: Optional[str] = None  # 🆕 Track GST input
    detailed_address: str
    area_name: str
    pincode: str
    city: str

class BuyerOnboardPayload(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str
    detailed_address: str
    area_name: str
    pincode: str
    city: str
class ProductCreatePayload(BaseModel):
    business_id: int
    product_name: str
    description: Optional[str] = None
    regular_price: float

# ==================== UPDATED VENDOR ONBOARDING ROUTE ====================

@app.post("/onboard-vendor/", status_code=status.HTTP_201_CREATED)
def onboard_local_vendor_profile(payload: VendorOnboardPayload, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Owner Email is already registered")
        
    target_area = db.query(Area).filter(Area.pincode == payload.pincode).first()
    if not target_area:
        target_area = Area(area_name=payload.area_name, pincode=payload.pincode, city=payload.city)
        db.add(target_area)
        db.flush()
        
    new_user = User(
        full_name=payload.full_name, email=payload.email, phone_number=payload.phone_number,
        role="vendor", area_id=target_area.id
    )
    db.add(new_user)
    db.flush()
    
    new_shop = Business(
        owner_id=new_user.id, 
        business_name=payload.business_name, 
        category=payload.category,
        detailed_address=payload.detailed_address, 
        gst_number=payload.gst_number,  # 🆕 Save verified GST registration numbers
        area_id=target_area.id
    )
    db.add(new_shop)
    db.commit()
    
    return {"status": "success", "message": "Onboarding complete!", "business_id": new_shop.id}

# ==================== DAILY DISCOVERY CATALOG ENDPOINTS ====================

@app.post("/products/", status_code=status.HTTP_201_CREATED)
def add_catalog_item(payload: ProductCreatePayload, db: Session = Depends(get_db)):
    shop = db.query(Business).filter(Business.id == payload.business_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Business profile not found")
        
    new_product = Product(
        business_id=payload.business_id, product_name=payload.product_name,
        description=payload.description, regular_price=payload.regular_price
    )
    db.add(new_product)
    db.commit()
    return {"status": "success", "message": "Product catalog item listed successfully"}

@app.get("/catalog/{business_id}")
def view_shop_digital_storefront(business_id: int, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.business_id == business_id, Product.is_available == True).all()
    return products

# ==================== CLEAN FRONTEND ROUTERS ====================

@app.get("/", response_class=HTMLResponse)
def read_root():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "index.html"), "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read(), status_code=200)

@app.get("/enroll-buyer", response_class=HTMLResponse)
def read_buyer_page():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "buyer.html"), "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read(), status_code=200)

@app.get("/enroll-seller", response_class=HTMLResponse)
def read_seller_page():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "seller.html"), "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read(), status_code=200)

# ==================== UNIFIED COMBINED ONBOARDING ENDPOINTS ====================

@app.post("/onboard-vendor/", status_code=status.HTTP_201_CREATED)
def onboard_local_vendor_profile(payload: VendorOnboardPayload, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Owner Email is already registered")
    if db.query(User).filter(User.phone_number == payload.phone_number).first():
        raise HTTPException(status_code=400, detail="Owner Phone Number is already registered")
        
    target_area = db.query(Area).filter(Area.pincode == payload.pincode).first()
    if not target_area:
        target_area = Area(area_name=payload.area_name, pincode=payload.pincode, city=payload.city)
        db.add(target_area)
        db.commit()
        db.refresh(target_area)
        
    new_user = User(
        full_name=payload.full_name, email=payload.email, phone_number=payload.phone_number,
        role="vendor", area_id=target_area.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    new_shop = Business(
        owner_id=new_user.id, business_name=payload.business_name, category=payload.category,
        detailed_address=payload.detailed_address, area_id=target_area.id
    )
    db.add(new_shop)
    db.commit()
    db.refresh(new_shop)
    
    return {"status": "success", "message": "Onboarding complete!", "business_id": new_shop.id}


@app.post("/onboard-buyer/", status_code=status.HTTP_201_CREATED)
def onboard_local_buyer_profile(payload: BuyerOnboardPayload, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email is already registered")
    if db.query(User).filter(User.phone_number == payload.phone_number).first():
        raise HTTPException(status_code=400, detail="Phone Number is already registered")
        
    target_area = db.query(Area).filter(Area.pincode == payload.pincode).first()
    if not target_area:
        target_area = Area(area_name=payload.area_name, pincode=payload.pincode, city=payload.city)
        db.add(target_area)
        db.commit()
        db.refresh(target_area)
        
    new_user = User(
        full_name=payload.full_name, email=payload.email, phone_number=payload.phone_number,
        role="customer", area_id=target_area.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"status": "success", "message": "Buyer registration complete!", "user_id": new_user.id}

# --- STANDARD ROUTE PATH RUNNERS ---

@app.get("/areas/")
def get_all_areas(db: Session = Depends(get_db)):
    return db.query(Area).filter(Area.is_active == True).all()

@app.post("/users/", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(full_name=user.full_name, email=user.email, phone_number=user.phone_number, role=user.role, area_id=user.area_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered", "user_id": new_user.id}

@app.get("/search/")
def search_marketplace_vendors(pincode: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Business).join(Area)
    if pincode:
        query = query.filter(Area.pincode == pincode)
    if category:
        query = query.filter(Business.category.ilike(f"%{category}%"))
    results = query.all()
    return {
        "count": len(results),
        "results": [{
            "shop_name": b.business_name, "category": b.category, "address": b.detailed_address,
            "area": b.area.area_name, "pincode": b.area.pincode, "verified": b.is_verified
        } for b in results]
    }
