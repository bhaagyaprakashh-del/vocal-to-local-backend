from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import engine, Base, get_db, Area, User, Business

# Sync database tables
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

# ==================== STATIC TEMPLATE CONTENT ====================
HTML_PART_1 = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vocal to Local | Discover Nearby Vendors</title>
    <link href="https://googleapis.com" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Poppins', sans-serif; }
        body { background: #f8fafc; color: #1e293b; }
        nav { background: rgba(79, 70, 229, 0.05); padding: 15px 40px; display: flex; justify-content: space-between; align-items: center; position: absolute; width: 100%; top: 0; left: 0; z-index: 10; }
        .logo { color: white; font-weight: 700; font-size: 1.3rem; text-decoration: none; }
        .nav-buttons { display: flex; gap: 15px; }
        .nav-btn { padding: 10px 22px; font-size: 0.9rem; font-weight: 600; border-radius: 30px; cursor: pointer; transition: 0.2s; text-decoration: none; border: none; }
        .btn-buyer { background: transparent; color: white; border: 2px solid white; }
        .btn-buyer:hover { background: white; color: #4f46e5; }
        .btn-seller { background: #10b981; color: white; box-shadow: 0 4px 12px rgba(16,185,129,0.3); }
        .btn-seller:hover { background: #059669; }
        header { background: linear-gradient(135deg, #4f46e5, #3730a3); color: white; padding: 140px 20px 80px 20px; text-align: center; box-shadow: 0 4px 20px rgba(79,70,229,0.15); }
        h1 { font-size: 3rem; font-weight: 700; margin-bottom: 15px; letter-spacing: -0.5px; }
        p { font-size: 1.2rem; opacity: 0.9; margin-bottom: 30px; font-weight: 300; }
        .search-container { background: white; max-width: 600px; margin: 0 auto; padding: 10px; border-radius: 50px; display: flex; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
        .search-container input { flex: 1; border: none; padding: 15px 25px; outline: none; font-size: 1rem; border-radius: 50px; }
        .search-container button { background: #4f46e5; color: white; border: none; padding: 15px 35px; font-weight: 600; border-radius: 50px; cursor: pointer; transition: 0.2s ease; }
        .search-container button:hover { background: #4338ca; }
        main { max-width: 1000px; margin: 50px auto; padding: 0 20px; }
        .section-title { font-size: 1.5rem; font-weight: 600; margin-bottom: 25px; border-left: 4px solid #4f46e5; padding-left: 10px; }
        .results-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; margin-top: 20px; }
        .shop-card { background: white; border-radius: 16px; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); border: 1px solid #e2e8f0; transition: transform 0.2s; }
        .shop-card:hover { transform: translateY(-5px); }
        .shop-name { font-size: 1.25rem; font-weight: 600; color: #0f172a; margin-bottom: 5px; }
        .shop-category { display: inline-block; background: #e0e7ff; color: #4338ca; font-size: 0.75rem; font-weight: 600; padding: 4px 12px; border-radius: 20px; margin-bottom: 15px; text-transform: uppercase; }
        .shop-meta { font-size: 0.9rem; color: #64748b; margin-top: 8px; display: flex; align-items: center; gap: 5px; }
        .no-results { text-align: center; color: #64748b; font-size: 1.1rem; grid-column: 1/-1; padding: 4px 0; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.6); z-index: 100; justify-content: center; align-items: center; backdrop-filter: blur(4px); }
        .modal-content { background: white; padding: 35px; border-radius: 20px; width: 100%; max-width: 450px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); position: relative; }
        .close-modal { position: absolute; top: 20px; right: 20px; font-size: 1.5rem; color: #94a3b8; cursor: pointer; border: none; background: none; }
        .modal h3 { font-size: 1.4rem; margin-bottom: 20px; color: #0f172a; }
        .form-group { margin-bottom: 18px; text-align: left; }
        .form-group label { display: block; font-size: 0.85rem; font-weight: 600; color: #475569; margin-bottom: 6px; }
        .form-group input { width: 100%; padding: 12px 16px; border: 1px solid #cbd5e1; border-radius: 10px; outline: none; font-size: 0.95rem; }
        .form-group input:focus { border-color: #4f46e5; }
        .submit-btn { width: 100%; background: #4f46e5; color: white; border: none; padding: 14px; border-radius: 12px; font-weight: 600; cursor: pointer; font-size: 1rem; margin-top: 10px; transition: 0.2s; }
        .submit-btn:hover { background: #4338ca; }
    </style>
</head>
<body>
    <nav>
        <a href="/" class="logo">📢 Vocal to Local</a>
        <div class="nav-buttons">
            <button class="nav-btn btn-buyer" onclick="openModal('buyerModal')">🙋‍♂️ Buyer Enrollment</button>
            <button class="nav-btn btn-seller" onclick="openModal('sellerModal')">🏪 Seller Enrollment</button>
        </div>
    </nav>
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
    <div id="buyerModal" class="modal">
        <div class="modal-content">
            <button class="close-modal" onclick="closeModal('buyerModal')">&times;</button>
            <h3>Buyer Registration</h3>
            <form id="buyerForm" onsubmit="submitForm(event, 'customer')">
                <div class="form-group"><label>Full Name</label><input type="text" id="b_name" required placeholder="John Doe"></div>
                <div class="form-group"><label>Email Address</label><input type="email" id="b_email" required placeholder="john@example.com"></div>
                <div class="form-group"><label>Phone Number</label><input type="text" id="b_phone" required placeholder="9876543210"></div>
                <button type="submit" class="submit-btn">Enroll as Buyer</button>
            </form>
        </div>
    </div>
    <div id="sellerModal" class="modal">
        <div class="modal-content">
            <button class="close-modal" onclick="closeModal('sellerModal')">&times;</button>
            <h3>Seller Registration</h3>
            <form id="sellerForm" onsubmit="submitForm(event, 'vendor')">
                <div class="form-group"><label>Full Name</label><input type="text" id="s_name" required placeholder="Rajesh Kumar"></div>
                <div class="form-group"><label>Email Address</label><input type="email" id="s_email" required placeholder="rajesh@example.com"></div>
                <div class="form-group"><label>Phone Number</label><input type="text" id="s_phone" required placeholder="9876543210"></div>
                <button type="submit" class="submit-btn">Enroll as Seller</button>
            </form>
        </div>
    </div>"""

HTML_PART_2 = """<script>
        function openModal(id) { document.getElementById(id).style.display = 'flex'; }
        function closeModal(id) { document.getElementById(id).style.display = 'none'; }
        async function submitForm(event, role) {
            event.preventDefault();
            const prefix = role === 'customer' ? 'b_' : 's_';
            const payload = {
                full_name: document.getElementById(prefix + 'name').value,
                email: document.getElementById(prefix + 'email').value,
                phone_number: document.getElementById(prefix + 'phone').value,
                role: role,
                area_id: null
            };
            try {
                const response = await fetch('/users/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();
                if (response.ok) {
                    alert('Enrollment Successful! Account Created.');
                    closeModal(role === 'customer' ? 'buyerModal' : 'sellerModal');
                    document.getElementById(role === 'customer' ? 'buyerForm' : 'sellerForm').reset();
                } else {
                    alert('Error: ' + data.detail);
                }
            } catch (error) {
                alert('Could not connect to registration server.');
            }
        }
        async function searchVendors() {
            const pincode = document.getElementById('pincodeInput').value.trim();
            const grid = document.getElementById('resultsGrid');
