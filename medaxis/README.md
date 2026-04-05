
# 🚀 MedAxis — AI-Powered Pharmacy Management Platform

> A scalable microservices system for modern pharmacy operations with AI-driven insights.

---

## ✨ Highlights

- 🔐 JWT Authentication with RBAC
- 📦 Real-time Inventory & Batch Tracking
- 💰 Smart Billing & Sales Processing
- 🤖 AI Insights & Natural Language Queries
- ⚡ Microservices Architecture (FastAPI)
A simplified but production-oriented microservices backend for a multi-store pharmacy chain.
Built with **Python (FastAPI)** + **PostgreSQL** + **Agentic AI (Claude API)**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   CLIENT / SWAGGER UI                │
└────────┬──────────┬──────────┬───────────┬──────────┘
         │          │          │           │
    :8001      :8002      :8003       :8004
┌────────▼─┐ ┌───────▼──┐ ┌──────▼──┐ ┌──▼────────┐
│  AUTH    │ │INVENTORY │ │ BILLING │ │    AI     │
│ SERVICE  │ │ SERVICE  │ │ SERVICE │ │  SERVICE  │
│          │ │          │ │         │ │           │
│ JWT/RBAC │ │ Products │ │Invoices │ │ Alerts    │
│ Users    │ │ Batches  │ │ Sales   │ │ Forecast  │
│ Roles    │ │ Stock    │ │ Reports │ │ Chat/LLM  │
└──────────┘ └──────────┘ └─────────┘ └───────────┘
         │          │           │
         └──────────┴───────────┘
                    │
           ┌────────▼────────┐
           │   PostgreSQL    │
           │  (shared DB)    │
           └─────────────────┘
```

## Service Ports

| Service           | Port | Description                              |
|-------------------|------|------------------------------------------|
| auth-service      | 8001 | JWT login, RBAC, user management         |
| inventory-service | 8002 | Products, batches, stock tracking        |
| billing-service   | 8003 | Invoices, OTC/Rx sales, daily summary    |
| ai-service        | 8004 | Alerts, demand forecast, AI chat         |

## User Roles & Permissions

| Role                  | Auth | Products | Stock | Billing | AI Alerts |
|-----------------------|------|----------|-------|---------|-----------|
| admin                 | ✅   | ✅ CRUD  | ✅    | ✅      | ✅        |
| store_manager         | ✅   | ✅ Read  | ✅    | ✅      | ✅        |
| pharmacist            | ✅   | ✅ Read  | Read  | ✅      | ✅        |
| inventory_supervisor  | ✅   | ✅ CRUD  | ✅    | Read    | ✅        |

---

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- pip

---

## Step-by-Step Setup

### 1. Clone / Download the project

```
medaxis/
├── auth-service/
├── inventory-service/
├── billing-service/
├── ai-service/
├── shared/
├── database/
├── .env.example
├── start_all.sh
└── README.md
```

### 2. Set up PostgreSQL

Install PostgreSQL if you haven't. Then run:

```bash
# Open psql as superuser
sudo -u postgres psql

# Inside psql, run:
\i database/init_db.sql
\q
```

Or manually:
```sql
CREATE USER medaxis WITH PASSWORD 'medaxis123';
CREATE DATABASE medaxis_db OWNER medaxis;
GRANT ALL PRIVILEGES ON DATABASE medaxis_db TO medaxis;
\c medaxis_db
GRANT ALL ON SCHEMA public TO medaxis;
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=postgresql://medaxis:medaxis123@localhost:5432/medaxis_db
SECRET_KEY=medaxis-super-secret-key-change-in-prod
INVENTORY_SERVICE_URL=http://localhost:8002
BILLING_SERVICE_URL=http://localhost:8003
ANTHROPIC_API_KEY=your-api-key-here   # optional, for AI chat feature
```

### 4. Install Dependencies (per service)

Option A — Install all at once:
```bash
pip install -r auth-service/requirements.txt
pip install -r inventory-service/requirements.txt
pip install -r billing-service/requirements.txt
pip install -r ai-service/requirements.txt
```

Option B — Use a single shared venv (recommended):
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary passlib[bcrypt] \
            python-jose[cryptography] pydantic[email] httpx
```

---

## Running the Services

### Option A — Run all with one script

```bash
chmod +x start_all.sh
./start_all.sh
```

### Option B — Run each service manually (4 terminals)

**Terminal 1 — Auth Service:**
```bash
cd auth-service
export DATABASE_URL=postgresql://medaxis:medaxis123@localhost:5432/medaxis_db
export SECRET_KEY=medaxis-super-secret-key-change-in-prod
uvicorn main:app --port 8001 --reload
```

**Terminal 2 — Inventory Service:**
```bash
cd inventory-service
export DATABASE_URL=postgresql://medaxis:medaxis123@localhost:5432/medaxis_db
export SECRET_KEY=medaxis-super-secret-key-change-in-prod
uvicorn main:app --port 8002 --reload
```

**Terminal 3 — Billing Service:**
```bash
cd billing-service
export DATABASE_URL=postgresql://medaxis:medaxis123@localhost:5432/medaxis_db
export SECRET_KEY=medaxis-super-secret-key-change-in-prod
export INVENTORY_SERVICE_URL=http://localhost:8002
uvicorn main:app --port 8003 --reload
```

**Terminal 4 — AI Service:**
```bash
cd ai-service
export SECRET_KEY=medaxis-super-secret-key-change-in-prod
export INVENTORY_SERVICE_URL=http://localhost:8002
export BILLING_SERVICE_URL=http://localhost:8003
export ANTHROPIC_API_KEY=your-key-here
uvicorn main:app --port 8004 --reload
```

---

## Load Sample Data

After all 4 services are running:

```bash
cd database
python seed_data.py
```

This creates:
- 4 users (admin, pharmacist, inventory supervisor, store manager)
- 6 products (OTC, prescription, wellness, equipment)
- 8 batches across 2 stores (including low-stock and near-expiry scenarios)
- 2 sample invoices

---

## API Documentation (Swagger UI)

| Service     | URL                              |
|-------------|----------------------------------|
| Auth        | http://localhost:8001/docs       |
| Inventory   | http://localhost:8002/docs       |
| Billing     | http://localhost:8003/docs       |
| AI          | http://localhost:8004/docs       |

---

## How Services Connect

```
Billing → calls → Inventory  (to deduct stock on every sale)
AI      → calls → Inventory  (to fetch low-stock, expiring batches)
AI      → calls → Billing    (to fetch daily sales for demand forecast)
All     → use   → Shared JWT (same SECRET_KEY validates tokens everywhere)
```

All services share the **same JWT secret key**, so a token issued by the
Auth Service is valid across Inventory, Billing, and AI services.

---

## Key API Flows

### 1. Login & Get Token
```
POST http://localhost:8001/auth/login
Body: { "username": "admin", "password": "Admin@123" }
→ Returns: { "access_token": "...", "role": "admin" }
```

### 2. Add Product (admin/inventory_supervisor only)
```
POST http://localhost:8002/products/
Header: Authorization: Bearer <token>
Body: { "name": "...", "sku": "...", "category": "otc", "unit_price": 50.0, "reorder_level": 20 }
```

### 3. Add Stock Batch
```
POST http://localhost:8002/batches/
Header: Authorization: Bearer <token>
Body: { "product_id": 1, "store_id": 1, "batch_number": "B001",
        "quantity": 100, "expiry_date": "2026-12-31", "purchase_price": 40.0 }
```

### 4. Create Invoice (sale)
```
POST http://localhost:8003/billing/invoices
Header: Authorization: Bearer <token>
Body: {
  "store_id": 1, "sale_type": "otc", "payment_method": "cash",
  "items": [{ "product_id": 1, "product_name": "Paracetamol 500mg",
               "batch_id": 1, "quantity": 5, "unit_price": 12.5 }]
}
→ Automatically deducts stock from Inventory Service
```

### 5. Get AI Alerts
```
GET http://localhost:8004/ai/alerts?store_id=1
Header: Authorization: Bearer <token>
→ Returns low-stock + expiry alerts with recommendations
```

### 6. Ask AI a Question
```
POST http://localhost:8004/ai/query
Header: Authorization: Bearer <token>
Body: { "question": "Which products are low on stock in store 1?", "store_id": 1 }
→ Claude answers using live inventory + sales data
```

---

## AI Guardrails

The AI service **blocks** any question related to:
- Medical diagnosis
- Drug dosage advice
- Treatment or prescription recommendations
- Drug interaction queries

These are redirected with a safe refusal message. The AI only answers
**operational** questions about stock, sales, and inventory.

---

## Non-Functional Design Decisions

| Concern         | Approach                                                      |
|-----------------|---------------------------------------------------------------|
| Scalability     | Each service runs independently, can be scaled separately     |
| Security        | JWT tokens, bcrypt passwords, role-based route guards         |
| Auditability    | StockMovement table logs every inventory change with user ID  |
| Reliability     | Billing rolls back if Inventory service is unreachable        |
| Observability   | /health endpoint on every service                             |
| Fault Tolerance | httpx timeouts on all inter-service calls                     |
| AI Safety       | Guardrails block medical/clinical queries                     |
