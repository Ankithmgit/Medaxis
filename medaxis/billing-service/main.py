from dotenv import load_dotenv
import os

# ✅ LOAD ENV FIRST
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.database import Base, engine
from models import Invoice, InvoiceItem  # noqa
from routes.billing_routes import router

# ✅ Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MedAxis Billing Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router)

@app.get("/health")
def health():
    return {"service": "billing-service", "status": "ok"}