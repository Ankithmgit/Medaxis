from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import enum
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.database import Base

class UserRole(str, enum.Enum):
    admin = "admin"
    pharmacist = "pharmacist"
    inventory_supervisor = "inventory_supervisor"
    store_manager = "store_manager"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    store_id = Column(Integer, nullable=True)   # None = regional/admin access
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
