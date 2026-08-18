from fastapi import FastAPI
from app.db.manager import init_db

app = FastAPI(title="shield-ai-api")

@app.on_event("startup")
async def _startup():
    try:
        await init_db()
    except Exception as exc:
        # In production, replace prints with structured logging; never expose raw exc to users
        print("[startup] DB init failed:", exc)

@app.get("/health")
async def health():
    return {"status": "ok"}
