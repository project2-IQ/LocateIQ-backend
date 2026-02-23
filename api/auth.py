from fastapi import APIRouter, HTTPException
from src.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    role = "Admin" if payload.email.endswith("@admin.com") else "Investor"
    return LoginResponse(message="Login successful", role=role)
