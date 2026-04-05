from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import uuid, httpx, os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from shared.database import get_db
from shared.auth_utils import get_current_user, require_roles
from models import Invoice, InvoiceItem
from schemas import InvoiceCreate, InvoiceOut

router = APIRouter(prefix="/billing", tags=["Billing"])

INVENTORY_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8002")

def generate_invoice_number():
    return f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

def deduct_stock_from_inventory(item, store_id: int, token: str):
    """Call inventory service to deduct stock after a sale."""
    payload = {
        "product_id": item.product_id,
        "store_id": store_id,
        "batch_id": item.batch_id,
        "quantity_change": -item.quantity,
        "note": f"Sale deduction - Invoice item"
    }
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = httpx.post(f"{INVENTORY_URL}/stock/adjust", json=payload, headers=headers, timeout=5.0)
        if resp.status_code != 200:
            raise HTTPException(400, f"Stock deduction failed for product {item.product_id}: {resp.text}")
    except httpx.RequestError:
        raise HTTPException(503, "Inventory service unreachable — sale aborted")

@router.post("/invoices", response_model=InvoiceOut)
def create_invoice(data: InvoiceCreate, db: Session = Depends(get_db),
                   current_user=Depends(require_roles("admin", "pharmacist", "store_manager")),
                   token: str = Depends(lambda req: req.headers.get("authorization", "").replace("Bearer ", ""))):
    # Validate prescription sales have a reference
    if data.sale_type == "prescription" and not data.prescription_ref:
        raise HTTPException(400, "Prescription reference required for prescription sales")

    subtotal = sum(item.quantity * item.unit_price for item in data.items)
    total = subtotal - data.discount + data.tax

    invoice = Invoice(
        invoice_number=generate_invoice_number(),
        store_id=data.store_id,
        sale_type=data.sale_type,
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        prescription_ref=data.prescription_ref,
        payment_method=data.payment_method,
        subtotal=subtotal,
        discount=data.discount,
        tax=data.tax,
        total=total,
        created_by=current_user.get("user_id"),
    )
    db.add(invoice)
    db.flush()  # get invoice.id

    for item_data in data.items:
        line_total = item_data.quantity * item_data.unit_price
        item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=item_data.product_id,
            product_name=item_data.product_name,
            batch_id=item_data.batch_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            line_total=line_total,
        )
        db.add(item)
        # Deduct from inventory
        deduct_stock_from_inventory(item_data, data.store_id, token)

    db.commit()
    db.refresh(invoice)
    return invoice

@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(store_id: int = Query(None), db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    query = db.query(Invoice)
    if store_id:
        query = query.filter(Invoice.store_id == store_id)
    return query.order_by(Invoice.created_at.desc()).limit(100).all()

@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    return invoice

@router.get("/summary/daily")
def daily_summary(store_id: int = Query(None), db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    from sqlalchemy import func, cast, Date
    query = db.query(
        cast(Invoice.created_at, Date).label("date"),
        func.count(Invoice.id).label("total_invoices"),
        func.sum(Invoice.total).label("total_revenue"),
        func.sum(Invoice.discount).label("total_discounts"),
    ).group_by(cast(Invoice.created_at, Date))
    if store_id:
        query = query.filter(Invoice.store_id == store_id)
    rows = query.order_by(cast(Invoice.created_at, Date).desc()).limit(30).all()
    return [{"date": str(r.date), "total_invoices": r.total_invoices,
             "total_revenue": r.total_revenue, "total_discounts": r.total_discounts} for r in rows]
