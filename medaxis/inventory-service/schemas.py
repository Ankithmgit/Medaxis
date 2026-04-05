from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from models import ProductCategory

class ProductCreate(BaseModel):
    name: str
    sku: str
    category: ProductCategory
    description: Optional[str] = None
    unit_price: float
    reorder_level: int = 10

class ProductOut(BaseModel):
    id: int
    name: str
    sku: str
    category: ProductCategory
    unit_price: float
    reorder_level: int

    class Config:
        from_attributes = True

class BatchCreate(BaseModel):
    product_id: int
    store_id: int
    batch_number: str
    quantity: int
    expiry_date: date
    purchase_price: float
    manufacturing_date: Optional[date] = None

class BatchOut(BaseModel):
    id: int
    product_id: int
    store_id: int
    batch_number: str
    quantity: int
    expiry_date: date
    purchase_price: float

    class Config:
        from_attributes = True

class StockSummary(BaseModel):
    product_id: int
    product_name: str
    store_id: int
    total_quantity: int
    reorder_level: int
    is_low_stock: bool

class StockAdjustment(BaseModel):
    product_id: int
    store_id: int
    batch_id: Optional[int] = None
    quantity_change: int
    note: Optional[str] = None
