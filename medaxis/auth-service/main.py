from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
import os

load_dotenv()
from shared.database import Base, engine
from models import User  # noqa: ensures table is registered
from routes.auth_routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MedAxis Auth Service", version="1.0.0", description="Authentication & RBAC for MedAxis")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

@app.get("/health")
def health():
    return {"service": "auth-service", "status": "ok"}
