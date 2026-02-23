
from fastapi import APIRouter

router = APIRouter(prefix="/investor", tags=["Investor"])


@router.get("/health")
def investor_health():
    return {"status": "Investor API is ready"}
