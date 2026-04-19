from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

from app.api import router


app = FastAPI(
    title="Facial Biometrics Backend",
    version="1.0.0",
    description="Backend API for facial biometric enrollment and verification.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://192.168.18.191:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root() -> Dict[str, str]:
    return {
        "service": "facial-biometrics-backend",
        "status": "running",
        "docs": "/docs",
    }
