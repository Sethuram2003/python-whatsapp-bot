from fastapi import FastAPI
from app.config import Settings
from app.api.routes.webhook import router as webhook_router

settings = Settings()

app = FastAPI(title="WhatsApp Bot API")

app.include_router(webhook_router, prefix="/webhook", tags=["webhook"])

@app.get("/")
async def root():
    return {"message": "WhatsApp Bot is running"}
