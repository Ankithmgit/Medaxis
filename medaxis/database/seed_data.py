"""
seed_data.py — Run this AFTER all services are started to populate sample data.
Usage: python seed_data.py
"""

import httpx, json

BASE_AUTH      = "http://localhost:8001"
BASE_INVENTORY = "http://localhost:8002"
BASE_BILLING   = "http://localhost:8003"

# ── Step 1: Register admin user ──────────────────────────────
print("Registering admin user...")
r = httpx.post(f"{BASE_AUTH}/auth/register", json={
    "username": "admin",
    "email": "admin@medaxis.com",
    "password": "Admin@123",
    "role": "admin",
    "store_id": None
})
print("  →", r.status_code, r.json())

# Register a pharmacist
r = httpx.post(f"{BASE_AUTH}/auth/register", json={
    "username": "pharma1",
    "email": "pharma1@medaxis.com",
    "password": "Pharma@123",
    "role": "pharmacist",
    "store_id": 1
})
print("  →", r.status_code, r.json())

# Register inventory supervisor
r = httpx.post(f"{BASE_AUTH}/auth/register", json={
    "username": "invsup1",
    "email": "invsup1@medaxis.com",
    "password": "Invsup@123",
    "role": "inventory_supervisor",
    "store_id": 1
})
print("  →", r.status_code, r.json())

# Register store manager
r = httpx.post(f"{BASE_AUTH}/auth/register", json={
    "username": "manager1",
    "email": "manager1@medaxis.com",
    "password": "Manager@123",
    "role": "store_manager",
    "store_id": 1
})
print("  →", r.status_code, r.json())

# ── Step 2: Login as admin ────────────────────────────────────
print("\nLogging in as admin...")
r = httpx.post(f"{BASE_AUTH}/auth/login", json={"username": "admin", "password": "Admin@123"})
token_data = r.json()
TOKEN = token_data["access_token"]
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
print("  → Token obtained")

# ── Step 3: Create products ───────────────────────────────────
print("\nCreating products...")
products = [
    {"name": "Paracetamol 500mg", "sku": "MED-PARA-500", "category": "otc",
     "unit_price": 12.5, "reorder_level": 50, "description": "Fever and pain relief"},
    {"name": "Amoxicillin 250mg", "sku": "MED-AMOX-250", "category": "prescription",
     "unit_price": 85.0, "reorder_level": 30, "description": "Antibiotic"},
    {"name": "Vitamin D3 1000IU", "sku": "WEL-VITD-1K", "category": "wellness",
     "unit_price": 220.0, "reorder_level": 20, "description": "Vitamin supplement"},
    {"name": "Cetirizine 10mg", "sku": "MED-CETI-10", "category": "otc",
     "unit_price": 35.0, "reorder_level": 40, "description": "Antihistamine"},
    {"name": "Metformin 500mg", "sku": "MED-METF-500", "category": "prescription",
     "unit_price": 45.0, "reorder_level": 25, "description": "Diabetes medication"},
    {"name": "BP Monitor Digital", "sku": "EQP-BPMON-01", "category": "equipment",
     "unit_price": 1800.0, "reorder_level": 5, "description": "Digital BP monitor"},
]

product_ids = []
for p in products:
    r = httpx.post(f"{BASE_INVENTORY}/products/", json=p, headers=HEADERS)
    pid = r.json().get("id")
    product_ids.append(pid)
    print(f"  → {p['name']}: {r.status_code} (id={pid})")

# ── Step 4: Add batches (with some low stock and near expiry) ─
print("\nAdding batches...")
from datetime import date, timedelta

batches = [
    # Normal stock
    {"product_id": product_ids[0], "store_id": 1, "batch_number": "B-PARA-001",
     "quantity": 200, "expiry_date": str(date.today() + timedelta(days=365)),
     "purchase_price": 8.0},
    # Low stock (below reorder level of 30)
    {"product_id": product_ids[1], "store_id": 1, "batch_number": "B-AMOX-001",
     "quantity": 15, "expiry_date": str(date.today() + timedelta(days=180)),
     "purchase_price": 60.0},
    # Expiring soon (10 days)
    {"product_id": product_ids[2], "store_id": 1, "batch_number": "B-VITD-001",
     "quantity": 50, "expiry_date": str(date.today() + timedelta(days=10)),
     "purchase_price": 170.0},
    # Normal
    {"product_id": product_ids[3], "store_id": 1, "batch_number": "B-CETI-001",
     "quantity": 120, "expiry_date": str(date.today() + timedelta(days=400)),
     "purchase_price": 25.0},
    # Very low stock
    {"product_id": product_ids[4], "store_id": 1, "batch_number": "B-METF-001",
     "quantity": 5, "expiry_date": str(date.today() + timedelta(days=200)),
     "purchase_price": 30.0},
    # Equipment - normal
    {"product_id": product_ids[5], "store_id": 1, "batch_number": "B-BP-001",
     "quantity": 8, "expiry_date": str(date.today() + timedelta(days=1825)),
     "purchase_price": 1400.0},
    # Store 2 data
    {"product_id": product_ids[0], "store_id": 2, "batch_number": "B-PARA-002",
     "quantity": 80, "expiry_date": str(date.today() + timedelta(days=300)),
     "purchase_price": 8.0},
    # Expiring in 5 days (critical)
    {"product_id": product_ids[3], "store_id": 2, "batch_number": "B-CETI-002",
     "quantity": 25, "expiry_date": str(date.today() + timedelta(days=5)),
     "purchase_price": 25.0},
]

batch_ids = []
for b in batches:
    r = httpx.post(f"{BASE_INVENTORY}/batches/", json=b, headers=HEADERS)
    bid = r.json().get("id")
    batch_ids.append(bid)
    print(f"  → Store {b['store_id']} batch {b['batch_number']}: {r.status_code} (id={bid})")

# ── Step 5: Create sample invoices ───────────────────────────
print("\nCreating sample invoices...")

# OTC sale - store 1
r = httpx.post(f"{BASE_BILLING}/billing/invoices", headers=HEADERS, json={
    "store_id": 1,
    "sale_type": "otc",
    "customer_name": "Ravi Kumar",
    "customer_phone": "9876543210",
    "payment_method": "upi",
    "discount": 5.0,
    "tax": 0.0,
    "items": [
        {"product_id": product_ids[0], "product_name": "Paracetamol 500mg",
         "batch_id": batch_ids[0], "quantity": 10, "unit_price": 12.5},
        {"product_id": product_ids[3], "product_name": "Cetirizine 10mg",
         "batch_id": batch_ids[3], "quantity": 5, "unit_price": 35.0},
    ]
})
print(f"  → OTC Invoice: {r.status_code}", r.json().get("invoice_number"))

# Prescription sale - store 1
r = httpx.post(f"{BASE_BILLING}/billing/invoices", headers=HEADERS, json={
    "store_id": 1,
    "sale_type": "prescription",
    "customer_name": "Priya Sharma",
    "customer_phone": "9123456789",
    "prescription_ref": "RX-2024-00123",
    "payment_method": "cash",
    "discount": 0.0,
    "tax": 18.0,
    "items": [
        {"product_id": product_ids[1], "product_name": "Amoxicillin 250mg",
         "batch_id": batch_ids[1], "quantity": 2, "unit_price": 85.0},
    ]
})
print(f"  → Prescription Invoice: {r.status_code}", r.json().get("invoice_number"))

print("\n✅ Seed data loaded successfully!")
print("\nTest credentials:")
print("  Admin:     admin / Admin@123")
print("  Pharmacist: pharma1 / Pharma@123")
print("  Inv. Sup.: invsup1 / Invsup@123")
print("  Manager:   manager1 / Manager@123")
print("\nAPI Docs:")
print("  Auth:      http://localhost:8001/docs")
print("  Inventory: http://localhost:8002/docs")
print("  Billing:   http://localhost:8003/docs")
print("  AI:        http://localhost:8004/docs")
