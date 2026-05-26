import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional

# ✅ FIXED: Added Product into the model import statement line cleanly
from app.database import engine, Base, get_db, Area, User, Business, Product

# ✅ FIXED: Commented out to prevent the SQLAlchemy metadata conflict crash on Render
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
    gst_number: Optional[str] = None  # ✅ Track GST input tracking strings
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

from fastapi import WebSocket, WebSocketDisconnect
import json

# Import your new database components cleanly
from app.database import AuctionRequest, AuctionBid

# ==================== WEB_SOCKET AUCTION ENGINE ====================

class HyperLocalAuctionManager:
    """Manages active live broadcast connections grouped exclusively by local Pincodes"""
    def __init__(self):
        # Dictionary format: { "411057": [WebSocket1, WebSocket2], "411033": [] }
        self.active_connections: dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, pincode: str):
        await websocket.accept()
        if pincode not in self.active_connections:
            self.active_connections[pincode] = []
        self.active_connections[pincode].append(websocket)

    def disconnect(self, websocket: WebSocket, pincode: str):
        if pincode in self.active_connections:
            self.active_connections[pincode].remove(websocket)

    async def broadcast_to_pincode(self, pincode: str, message: dict):
        """Sends updates strictly to buyers and sellers operating inside the same circle radius"""
        if pincode in self.active_connections:
            for connection in self.active_connections[pincode]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    # Clear dead references if a browser tab closed abruptly
                    self.active_connections[pincode].remove(connection)

auction_manager = HyperLocalAuctionManager()

# ==================== BROADCAST ENDPOINT ROUTE ====================

@websocket_route := app.websocket("/ws/auction/{pincode}")
async def live_auction_stream(websocket: WebSocket, pincode: str):
    await auction_manager.connect(websocket, pincode)
    db: Session = next(get_db()) # Initialize a dedicated stream session instance
    
    try:
        while True:
            # Continuously monitor live traffic coming down the wire channel stream
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            
            # Action A: Buyer broadcasts a brand new shopping list request live
            if data.get("action") == "new_request":
                new_request = AuctionRequest(
                    buyer_id=data["buyer_id"],
                    items_list=data["items_list"],
                    target_pincode=pincode,
                    max_budget=float(data["max_budget"])
                )
                db.add(new_request)
                db.commit()
                db.refresh(new_request)
                
                # Instantly alert all merchants inside the pin zone radius card
                await auction_manager.broadcast_to_pincode(pincode, {
                    "event": "request_created",
                    "auction_id": new_request.id,
                    "items": new_request.items_list,
                    "budget": new_request.max_budget
                })

            # Action B: Merchant drops a lower counter-bid price to beat corporate competition
            elif data.get("action") == "place_bid":
                new_bid = AuctionBid(
                    auction_id=int(data["auction_id"]),
                    business_id=int(data["business_id"]),
                    bid_amount=float(data["bid_amount"]),
                    delivery_time=data.get("delivery_time", "30 Mins")
                )
                db.add(new_bid)
                db.commit()
                
                # Instantly sync both buyer and cross-competing store feeds in real-time
                await auction_manager.broadcast_to_pincode(pincode, {
                    "event": "bid_received",
                    "auction_id": new_bid.auction_id,
                    "business_id": new_bid.business_id,
                    "new_low_price": new_bid.bid_amount,
                    "delivery": new_bid.delivery_time
                })
                
    except WebSocketDisconnect:
        auction_manager.disconnect(websocket, pincode)
    finally:
        db.close()


# ==================== CLEAN FRONTEND ROUTERS ====================

@app.get("/", response_class=HTMLResponse)
def read_root():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "index.html"), "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read(), status_code=200)
        
@app.get("/saturday-sale", response_class=HTMLResponse)
def read_saturday_auction_arena():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "auction.html"), "r", encoding="utf-8") as file:
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

@app.post("/onboard-vendor", status_code=status.HTTP_201_CREATED)
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
        owner_id=new_user.id, 
        business_name=payload.business_name, 
        category=payload.category,
        detailed_address=payload.detailed_address, 
        gst_number=payload.gst_number,  # ✅ Cleanly populates the new vendor field variables
        area_id=target_area.id
    )
    db.add(new_shop)
    db.commit()
    db.refresh(new_shop)
    
    return {"status": "success", "message": "Onboarding complete!", "business_id": new_shop.id}


@app.post("/onboard-buyer", status_code=status.HTTP_201_CREATED)
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
        role="customer", area_id=target_area.id, detailed_address=payload.detailed_address
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"status": "success", "message": "Buyer registration complete!", "user_id": new_user.id}

# ==================== DAILY DISCOVERY CATALOG ENDPOINTS ====================

@app.post("/products", status_code=status.HTTP_201_CREATED)
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

# --- STANDARD ROUTE PATH RUNNERS ---

@app.get("/areas")
def get_all_areas(db: Session = Depends(get_db)):
    return db.query(Area).filter(Area.is_active == True).all()

@app.post("/users", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(full_name=user.full_name, email=user.email, phone_number=user.phone_number, role=user.role, area_id=user.area_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered", "user_id": new_user.id}

# ✅ FIXED: Completed the broken dynamic search routing logic cleanly
@app.get("/search")
def search_marketplace_vendors(pincode: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Business).join(Area)
    if pincode:
        query = query.filter(Area.pincode == pincode)
    if category:
        query = query.filter(Business.category.ilike(f"%{category}%"))
    results = query.all()
    
    return [
        {
            "id": b.id,
            "business_name": b.business_name,
            "category": b.category,
            "detailed_address": b.detailed_address,
            "gst_number": b.gst_number,
            "pincode": b.area.pincode
        } for b in results
    ]
