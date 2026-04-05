from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.database import Base

class ProductCategory(str, enum.Enum):
    otc = "otc"
    prescription = "prescription"
    wellness = "wellness"
    equipment = "equipment"

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    sku = Column(String, unique=True, nullable=False)
    category = Column(Enum(ProductCategory), nullable=False)
    description = Column(Text, nullable=True)
    unit_price = Column(Float, nullable=False)
    reorder_level = Column(Integer, default=10)  # alert threshold
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    batches = relationship("Batch", back_populates="product")

class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    store_id = Column(Integer, nullable=False)
    batch_number = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    manufacturing_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False)
    purchase_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="batches")

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    store_id = Column(Integer, nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=True)
    movement_type = Column(String, nullable=False)  # "sale", "restock", "adjustment", "expiry_removal"
    quantity_change = Column(Integer, nullable=False)  # negative for deductions
    note = Column(String, nullable=True)
    created_by = Column(Integer, nullable=True)  # user_id
    created_at = Column(DateTime(timezone=True), server_default=func.now())
