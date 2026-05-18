"""OverCloud Backend - Main FastAPI Application.

This is the entry point for the OverCloud backend API.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.core.logging import setup_logging

# Setup logging BEFORE creating app
setup_logging(
    level=settings.LOG_LEVEL,
    json_format=settings.LOG_JSON_FORMAT,
    enable_cloudwatch=settings.ENABLE_CLOUDWATCH,
    enable_sentry=settings.ENABLE_SENTRY,
    sentry_dsn=settings.SENTRY_DSN,
    environment=settings.ENV,
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="OverCloud API",
    description="Cloud infrastructure management platform - Requirements-driven IaC generation",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # XSS Protection (legacy, but doesn't hurt)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # HSTS (only for HTTPS)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Content Security Policy
    if settings.ENV == "production":
        # Frontend needs inline scripts for Vite HMR
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.overcloud.io;"
        )
    else:
        # Dev: Allow Vite HMR
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self' ws: http://localhost:*;"
        )

    return response


# Custom Exception Handlers (hide internals in production)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions - hide details in production."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors - sanitize in production."""
    if settings.ENV == "production":
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Invalid request data"}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()}
        )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions - never expose internals in production."""
    # Log error with context
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
        }
    )

    if settings.ENV == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )
    else:
        # Development: show full traceback
        raise exc


@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info(
        "OverCloud API starting",
        extra={
            "version": "0.1.0",
            "environment": settings.ENV,
            "debug": settings.DEBUG,
            "log_level": settings.LOG_LEVEL,
        }
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
from app.api import (
    admin,
    architectures,
    audit,
    auth,
    aws_credentials,
    billing,
    blueprints,
    cidr,
    costs,
    data_upload,
    deployments,
    designer,
    organisations,
    terraform,
    users,
    validation,
    voucher,
    websockets,
)
from app.api import (
    dsgvo,
    webhooks as webhooks_module,  # Renamed to avoid conflict with websockets
)

# Authentication & User Management
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(organisations.router, prefix="/api/v1/organisations", tags=["organisations"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["billing"])

# AWS Integration
app.include_router(aws_credentials.router, prefix="/api/v1", tags=["aws-credentials"])
app.include_router(data_upload.router, prefix="/api/v1", tags=["data-upload"])

# Admin Endpoints (SuperAdmin only)
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])

# Vouchers (Authenticated + Admin)
app.include_router(voucher.router, tags=["vouchers"])

# Core Features
app.include_router(validation.router, prefix="/api/v1", tags=["validation"])
app.include_router(blueprints.router, prefix="/api/v1", tags=["blueprints"])
app.include_router(architectures.router, prefix="/api/v1", tags=["architectures"])
app.include_router(costs.router, prefix="/api/v1", tags=["costs"])
app.include_router(deployments.router, prefix="/api/v1", tags=["deployments"])
app.include_router(terraform.router, prefix="/api/v1", tags=["terraform"])
app.include_router(websockets.router, prefix="/api/v1", tags=["websockets"])
app.include_router(audit.router, prefix="/api/v1", tags=["audit"])
app.include_router(cidr.router, prefix="/api/v1", tags=["cidr"])
app.include_router(designer.router, prefix="/api/v1", tags=["designer"])

# DSGVO / GDPR Endpoints
app.include_router(dsgvo.router, tags=["dsgvo"])

# Webhooks (no auth required)
app.include_router(webhooks_module.router, prefix="/webhooks", tags=["webhooks"])


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
