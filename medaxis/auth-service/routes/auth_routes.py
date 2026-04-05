from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.database import get_db
from shared.auth_utils import create_access_token, get_current_user
from models import User
from schemas import UserCreate, UserOut, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 🔐 Password helpers
def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)


# 🟢 Register
@router.post("/register", response_model=UserOut)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        store_id=user_data.store_id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# 🔑 Login (FIXED FOR SWAGGER OAuth2)
@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({
        "sub": user.username,
        "role": user.role,
        "user_id": user.id,
        "store_id": user.store_id
    })

    return TokenResponse(
        access_token=token,
        role=user.role,
        user_id=user.id
    )


# 👤 Get current user
@router.get("/me", response_model=UserOut)
def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == current_user["sub"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# 👥 List users (admin / manager)
@router.get("/users", response_model=list[UserOut])
def list_users(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") not in ["admin", "store_manager"]:
        raise HTTPException(status_code=403, detail="Admins/Store Managers only")

    return db.query(User).all()


# 🚫 Deactivate user
@router.patch("/users/{user_id}/deactivate")
def deactivate_user(user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()

    return {"message": f"User {user.username} deactivated"}