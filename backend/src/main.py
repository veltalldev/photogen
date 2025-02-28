from fastapi import FastAPI
from core.config import settings, validate_settings
import logging

# Initialize logging
from core.logging_config import setup_logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application...")
    if not validate_settings():
        raise Exception("Settings validation failed")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
