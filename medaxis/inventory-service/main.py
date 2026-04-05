from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


from dotenv import load_dotenv
import os

load_dotenv()

from shared.database import Base, engine
from models import Product, Batch, StockMovement  # noqa
from routes.inventory_routes import product_router, batch_router, stock_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MedAxis Inventory Service", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(product_router)
app.include_router(batch_router)
app.include_router(stock_router)

@app.get("/health")
def health():
    return {"service": "inventory-service", "status": "ok"}
