from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.database import get_db
from shared.auth_utils import get_current_user, require_roles
from models import Product, Batch, StockMovement
from schemas import ProductCreate, ProductOut, BatchCreate, BatchOut, StockSummary, StockAdjustment

product_router = APIRouter(prefix="/products", tags=["Products"])
batch_router = APIRouter(prefix="/batches", tags=["Batches"])
stock_router = APIRouter(prefix="/stock", tags=["Stock"])

# ── Products ────────────────────────────────────────────────
@product_router.post("/", response_model=ProductOut)
def create_product(data: ProductCreate, db: Session = Depends(get_db),
                   current_user=Depends(require_roles("admin", "inventory_supervisor"))):
    if db.query(Product).filter(Product.sku == data.sku).first():
        raise HTTPException(400, "SKU already exists")
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@product_router.get("/", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(Product).all()

@product_router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    return product

# ── Batches ─────────────────────────────────────────────────
@batch_router.post("/", response_model=BatchOut)
def add_batch(data: BatchCreate, db: Session = Depends(get_db),
              current_user=Depends(require_roles("admin", "inventory_supervisor", "store_manager"))):
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    batch = Batch(**data.model_dump())
    db.add(batch)
    # Log stock movement
    movement = StockMovement(
        product_id=data.product_id,
        store_id=data.store_id,
        batch_id=None,
        movement_type="restock",
        quantity_change=data.quantity,
        note=f"Batch {data.batch_number} added",
        created_by=current_user.get("user_id"),
    )
    db.add(movement)
    db.commit()
    db.refresh(batch)
    return batch

@batch_router.get("/store/{store_id}", response_model=list[BatchOut])
def get_store_batches(store_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(Batch).filter(Batch.store_id == store_id).all()

@batch_router.get("/expiring-soon")
def expiring_soon(days: int = Query(30), store_id: int = Query(None),
                  db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    threshold = date.today() + timedelta(days=days)
    query = db.query(Batch).filter(Batch.expiry_date <= threshold, Batch.quantity > 0)
    if store_id:
        query = query.filter(Batch.store_id == store_id)
    batches = query.all()
    result = []
    for b in batches:
        product = db.query(Product).filter(Product.id == b.product_id).first()
        result.append({
            "batch_id": b.id,
            "product_name": product.name if product else "Unknown",
            "sku": product.sku if product else "",
            "store_id": b.store_id,
            "batch_number": b.batch_number,
            "quantity": b.quantity,
            "expiry_date": b.expiry_date.isoformat(),
            "days_until_expiry": (b.expiry_date - date.today()).days,
        })
    return sorted(result, key=lambda x: x["days_until_expiry"])

# ── Stock ────────────────────────────────────────────────────
@stock_router.get("/summary")
def stock_summary(store_id: int = Query(None), db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    products = db.query(Product).all()
    result = []
    for p in products:
        query = db.query(func.sum(Batch.quantity)).filter(Batch.product_id == p.id, Batch.quantity > 0)
        if store_id:
            query = query.filter(Batch.store_id == store_id)
        total = query.scalar() or 0
        result.append(StockSummary(
            product_id=p.id,
            product_name=p.name,
            store_id=store_id or 0,
            total_quantity=total,
            reorder_level=p.reorder_level,
            is_low_stock=total <= p.reorder_level,
        ))
    return result

@stock_router.post("/adjust")
def adjust_stock(data: StockAdjustment, db: Session = Depends(get_db),
                 current_user=Depends(require_roles("admin", "inventory_supervisor", "store_manager"))):
    if data.batch_id:
        batch = db.query(Batch).filter(Batch.id == data.batch_id).first()
        if not batch:
            raise HTTPException(404, "Batch not found")
        batch.quantity += data.quantity_change
        if batch.quantity < 0:
            raise HTTPException(400, "Insufficient stock in batch")
    movement = StockMovement(
        product_id=data.product_id,
        store_id=data.store_id,
        batch_id=data.batch_id,
        movement_type="adjustment",
        quantity_change=data.quantity_change,
        note=data.note,
        created_by=current_user.get("user_id"),
    )
    db.add(movement)
    db.commit()
    return {"message": "Stock adjusted successfully"}

@stock_router.get("/movements/{product_id}")
def stock_movements(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    movements = db.query(StockMovement).filter(StockMovement.product_id == product_id).order_by(StockMovement.created_at.desc()).limit(50).all()
    return movements

@stock_router.get("/low-stock")
def low_stock_alerts(store_id: int = Query(None), db: Session = Depends(get_db),
                     current_user=Depends(get_current_user)):
    products = db.query(Product).all()
    alerts = []
    for p in products:
        query = db.query(func.sum(Batch.quantity)).filter(Batch.product_id == p.id, Batch.quantity > 0)
        if store_id:
            query = query.filter(Batch.store_id == store_id)
        total = query.scalar() or 0
        if total <= p.reorder_level:
            alerts.append({
                "product_id": p.id,
                "product_name": p.name,
                "sku": p.sku,
                "current_stock": total,
                "reorder_level": p.reorder_level,
                "deficit": p.reorder_level - total,
            })
    return alerts
