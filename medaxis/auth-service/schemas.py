from pydantic import BaseModel, EmailStr
from typing import Optional
from models import UserRole

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole
    store_id: Optional[int] = None

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    store_id: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
