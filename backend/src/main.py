from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.config import settings, validate_settings
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db.database import get_db

# Initialize logging
from core.logging_config import setup_logging
logger = setup_logging()

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application...")
    if not validate_settings():
        raise Exception("Settings validation failed")
    logger.info("Settings validated successfully")
    
    yield  # Run the app
    
    # Shutdown
    logger.info("Shutting down application...")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

# Health check endpoint
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        # Test database connection with proper SQL text declaration
        logger.info("Testing database connection...")
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        logger.info(f"Database query result: {value}")
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        db_status = "disconnected"

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.API_VERSION,
        "database": db_status
    }
