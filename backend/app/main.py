"""
FastAPI Main Application Entry Point
Finance Assistant Backend
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routes
from app.routes import (
    auth_routes,
    user_routes,
    account_routes,
    transaction_routes,
    budget_routes,
    ml_routes,
    chatbot_routes,
    report_routes
)

# Import middleware
from app.middlewares.auth_middleware import AuthMiddleware
from app.middlewares.logging_middleware import LoggingMiddleware

# Import database
from app.models.database import engine, Base
from app.utils.ml_model_loader import load_models

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Finance Assistant Backend...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Load ML models
    await load_models()
    logger.info("ML models loaded")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Finance Assistant Backend...")

# Create FastAPI application
app = FastAPI(
    title="Finance Assistant API",
    description="Comprehensive personal finance management with AI insights",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Security scheme
security = HTTPBearer()

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost").split(",")
)

app.add_middleware(AuthMiddleware)
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(user_routes.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(account_routes.router, prefix="/api/v1/accounts", tags=["Accounts"])
app.include_router(transaction_routes.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(budget_routes.router, prefix="/api/v1/budgets", tags=["Budgets"])
app.include_router(ml_routes.router, prefix="/api/v1/ml", tags=["Machine Learning"])
app.include_router(chatbot_routes.router, prefix="/api/v1/chatbot", tags=["Chatbot"])
app.include_router(report_routes.router, prefix="/api/v1/reports", tags=["Reports"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Finance Assistant API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "finance-assistant-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )