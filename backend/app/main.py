"""OverCloud Backend - Main FastAPI Application.

This is the entry point for the OverCloud backend API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# Create FastAPI app
app = FastAPI(
    title="OverCloud API",
    description="Cloud infrastructure management platform - Requirements-driven IaC generation",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - Health check."""
    return {
        "message": "OverCloud API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
    }


# API Routes
from app.api import validation, architectures, costs, deployments, websockets, audit

app.include_router(validation.router, prefix="/api/v1", tags=["validation"])
app.include_router(architectures.router, prefix="/api/v1", tags=["architectures"])
app.include_router(costs.router, prefix="/api/v1", tags=["costs"])
app.include_router(deployments.router, prefix="/api/v1", tags=["deployments"])
app.include_router(websockets.router, prefix="/api/v1", tags=["websockets"])
app.include_router(audit.router, prefix="/api/v1", tags=["audit"])


if __name__ == "__main__":
    import uvicorn

    # Use configurable host/port from settings
    # For Docker/containers: Set HOST=0.0.0.0 in .env
    # For local dev: Default 127.0.0.1 (localhost only) is secure
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
