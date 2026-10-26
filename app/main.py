# app/main.py
from fastapi import FastAPI
from app.routes.analytics import router

app = FastAPI(title="Umami Analytics Backend")

@app.get("/")
def root():
    return {"message": "Umami and clarity Analytics API is running"}

app.include_router(router)
# & "D:\New folder (11)\.venv\Scripts\Activate.ps1"
# uvicorn app.main:app --reload


