
from fastapi import FastAPI

from src.api.auth import router as auth_router
from src.api.investor import router as investor_router

app = FastAPI(title="LocateIQ Backend")

app.include_router(auth_router)
app.include_router(investor_router)


@app.get("/")
def root():
    return {"message": "LocateIQ backend is running"}
