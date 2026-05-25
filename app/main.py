from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import engine, Base, get_db, Area, User, Business

# Sync models to database schema
Base.metadata.create_all(bind=engine)
# Temporary clean command to clear old structural conflicts
Base.metadata.drop_all(bind=engine)

# Sync models to database schema
Base.metadata.create_all(bind=engine)


app = FastAPI(title="Vocal to Local API")

# ==================== PYDANTIC VALDIATION SCHEMAS ====================
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

# ==================== BEAUTIFUL FRONTEND HOME ENTRY ====================

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vocal to Local | Discover Nearby Vendors</title>
        <link href="https://googleapis.com" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Poppins', sans-serif; }
            body { background: #f8fafc; color: #1e293b; }
            header { background: linear-gradient(135deg, #4f46e5, #3730a3); color: white; padding: 80px 20px; text-align: center; box-shadow: 0 4px 20px rgba(79,70,229,0.15); }
            h1 { font-size: 3rem; font-weight: 700; margin-bottom: 15px; letter-spacing: -0.5px; }
            p { font-size: 1.2rem; opacity: 0.9; margin-bottom: 30px; font-weight: 300; }
            .search-container { background: white; max-width: 600px; margin: 0 auto; padding: 10px; border-radius: 50px; display: flex; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
            .search-container input { flex: 1; border: none; padding: 15px 25px; outline: none; font-size: 1rem; border-radius: 50px; }
            .search-container button { background: #4f46e5; color: white; border: none; padding: 15px 35px; font-weight: 600; border-radius: 50px; cursor: pointer; transition: 0.2s ease; }
            .search-container button:hover { background: #4338ca; }
            main { max-width: 1000px; margin: 50px auto; padding: 0 20px; }
            .section-title { font-size: 1.5rem; font-weight: 600; margin-bottom: 25px; border-left: 4px solid #4f46e5; padding-left: 10px; }
            .results-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 100fr)); gap: 25px; margin-top: 20px; }
            .shop-card { background: white; border-radius: 16px; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); border: 1px solid #e2e8f0; transition: transform 0.2s; }
            .shop-card:hover { transform: translateY(-5px); }
            .shop-name { font-size: 1.25rem; font-weight: 600; color: #0f172a; margin-bottom: 5px; }
            .shop-category { display: inline-block; background: #e0e7ff; color: #4338ca; font-size: 0.75rem; font-weight: 600; padding: 4px 12px; border-radius: 20px; margin-bottom: 15px; text-transform: uppercase; }
            .shop-meta { font-size: 0.9rem; color: #64748b; margin-top: 8px; display: flex; align-items: center; gap: 5px; }
            .no-results { text-align: center; color: #64748b; font-size: 1.1rem; grid-column: 1/-1; padding: 4px 0; }
        </style>
    </head>
    <body>
        <header>
            <h1>Vocal to Local Marketplace</h1>
            <p>Empowering local small vendors and neighborhoods</p>
            <div class="search-container">
                <input type="text" id="pincodeInput" placeholder="Enter your Location Pincode (e.g., 411057)..." maxlength="10">
                <button onclick="searchVendors()">Search Shops</button>
            </div>
        </header>
        <main>
            <h2 class="section-title">Available Local Vendors</h2>
            <div class="results-grid" id="resultsGrid">
                <div class="no-results">Use the search box above to find local shops in your operational pin area.</div>
            </div>
        </main>
        <script>
            async function searchVendors() {
                const pincode = document.getElementById('pincodeInput').value.trim();
                const grid = document.getElementById('resultsGrid');
                if (!pincode) { alert('Please type a valid pincode first!'); return; }
                grid.innerHTML = '<div class="no-results">Searching database profiles...</div>';
                try {
                    const response = await fetch(`/search/?pincode=${pincode}`);
                    const data = await response.json();
                    grid.innerHTML = '';
                    if (data.count === 0) {
                        grid.innerHTML = '<div class="no-results">No registered local vendors found matching this pincode yet.</div>';
                        return;
                    }
                    data.results.forEach(shop => {
                        grid.innerHTML += `
                            <div class="shop-card">
                                <div class="shop-name">${shop.shop_name}</div>
                                <span class="shop-category">${shop.category}</span>
                                <div class="shop-meta">📍 <b>Address:</b> ${shop.address}</div>
                                <div class="shop-meta">🏢 <b>Area:</b> ${shop.area} (${shop.pincode})</div>
                            </div>
                        `;
                    });
                } catch (error) {
                    grid.innerHTML = '<div class="no-results" style="color: red;">Error accessing the live marketplace API.</div>';
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

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
