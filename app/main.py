from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import engine, Base, get_db, Area, User

# Sync models to live database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vocal to Local API")

# ==================== PYDANTIC SCHEMAS (DATA VALIDATION) ====================
class AreaCreate(BaseModel):
    area_name: str
    pincode: str
    city: str

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str
    role: str = "customer" # customer or vendor
    area_id: Optional[int] = None

# ==================== API ENDPOINTS ====================

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Welcome to Vocal to Local API"}

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
    # Check if email or phone already exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.phone_number == user.phone_number).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # Verify area exists if provided
    if user.area_id and not db.query(Area).filter(Area.id == user.area_id).first():
        raise HTTPException(status_code=404, detail="Specified Area ID not found")

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        role=user.role,
        area_id=user.area_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id}

@app.get("/users/")
def get_all_users(db: Session = Depends(get_db)):
    return db.query(User).all()
