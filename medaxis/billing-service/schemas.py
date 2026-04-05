from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models import SaleType, PaymentMethod

class InvoiceItemCreate(BaseModel):
    product_id: int
    product_name: str
    batch_id: Optional[int] = None
    quantity: int
    unit_price: float

class InvoiceCreate(BaseModel):
    store_id: int
    sale_type: SaleType
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    prescription_ref: Optional[str] = None
    payment_method: PaymentMethod
    discount: float = 0.0
    tax: float = 0.0
    items: List[InvoiceItemCreate]

class InvoiceItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    line_total: float

    class Config:
        from_attributes = True

class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    store_id: int
    sale_type: SaleType
    customer_name: Optional[str]
    payment_method: PaymentMethod
    subtotal: float
    discount: float
    tax: float
    total: float
    created_by: int
    created_at: datetime
    items: List[InvoiceItemOut]

    class Config:
        from_attributes = True
