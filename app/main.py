import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import engine, Base, get_db, Area, User, Business

# Sync database tables schema layouts
Base.metadata.create_all(bind=engine)

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

# ==================== CLEAN FRONTEND HOME ROUTER ====================

@app.get("/", response_class=HTMLResponse)
def read_root():
    # Safely load the frontend template file directly from the app folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "index.html")
    
    with open(file_path, "r", encoding="utf-8") as file:
        html_layout_markup = file.read()
        
    return HTMLResponse(content=html_layout_markup, status_code=200)

# --- AREA ENDPOINTS ---
@app.post("/areas/", status_code=status.HTTP_201_CREATED)
def create_new_area(area: AreaCreate, db: Session = Depends(get_db)):
    db_area = db.query(Area).filter(Area.area_name == area.area_name).first()
    if db_area:
        raise HTTPException(status_code=400, detail="Area name already registered")
    new_area = Area(area_name=area.area_name, pincode=area.pincode, city=area.city)
    db.add(new_area)
    db.commit()
    db.refresh(new_area)
    return {"message": "Area added successfully", "area_id": new_area.id, "area_name": new_area.area_name}

@app.get("/areas/")
def get_all_areas(db: Session = Depends(get_db)):
    return db.query(Area).filter(Area.is_active == True).all()

# --- USER ENDPOINTS ---
@app.post("/users/", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.phone_number == user.phone_number).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")
    if user.area_id and not db.query(Area).filter(Area.id == user.area_id).first():
        raise HTTPException(status_code=404, detail="Specified Area ID not found")

    new_user = User(full_name=user.full_name, email=user.email, phone_number=user.phone_number, role=user.role, area_id=user.area_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id}

@app.get("/users/")
def get_all_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# --- BUSINESS ENDPOINTS ---
@app.post("/businesses/", status_code=status.HTTP_201_CREATED)
def register_business(biz: BusinessCreate, db: Session = Depends(get_db)):
    owner = db.query(User).filter(User.id == biz.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner User ID not found")
    if owner.role != "vendor":
        raise HTTPException(status_code=400, detail="User must have 'vendor' role to register a shop")
    if not db.query(Area).filter(Area.id == biz.area_id).first():
        raise HTTPException(status_code=404, detail="Specified Area ID does not exist")

    new_shop = Business(owner_id=biz.owner_id, business_name=biz.business_name, category=biz.category, detailed_address=biz.detailed_address, area_id=biz.area_id)
    db.add(new_shop)
    db.commit()
    db.refresh(new_shop)
    return {"message": "Local shop onboarding successful!", "business_id": new_shop.id}

# --- SEARCH MARKETPLACE ENDPOINT ---
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
