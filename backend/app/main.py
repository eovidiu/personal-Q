"""
ABOUTME: Main FastAPI application entry point with rate limiting and CORS.
ABOUTME: Configures all routers, middleware, and lifecycle events.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config.settings import settings
from app.db.database import init_db, close_db
from app.middleware.rate_limit import limiter
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.logging_middleware import RequestLoggingMiddleware, request_id_var
from app.services.cache_service import cache_service
from app.utils.datetime_utils import utcnow
from app.exceptions import (
    PersonalQException,
    AgentNotFoundException,
    TaskNotFoundException,
    LLMServiceError,
    IntegrationError,
    ConfigurationError
)


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Personal-Q AI Agent Manager...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize cache
    await cache_service.connect()
    logger.info("Cache service initialized")

    yield

    # Cleanup
    logger.info("Shutting down...")
    await cache_service.close()
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Agent Management System with CrewAI orchestration",
    lifespan=lifespan,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json"
)

# Global exception handlers for consistent error responses

# Custom application exceptions
@app.exception_handler(AgentNotFoundException)
async def agent_not_found_handler(request: Request, exc: AgentNotFoundException):
    """Handle agent not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Not Found",
            "detail": str(exc) or "Agent not found",
            "code": "AGENT_NOT_FOUND",
            "timestamp": utcnow().isoformat(),
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
        }
    )


@app.exception_handler(TaskNotFoundException)
async def task_not_found_handler(request: Request, exc: TaskNotFoundException):
    """Handle task not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Not Found",
            "detail": str(exc) or "Task not found",
            "code": "TASK_NOT_FOUND",
            "timestamp": utcnow().isoformat(),
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
        }
    )


@app.exception_handler(LLMServiceError)
async def llm_service_error_handler(request: Request, exc: LLMServiceError):
    """Handle LLM service errors."""
    logger.error(f"LLM service error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Service Unavailable",
            "detail": "LLM service is temporarily unavailable",
            "code": "LLM_SERVICE_ERROR",
            "timestamp": utcnow().isoformat(),
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
        }
    )


@app.exception_handler(IntegrationError)
async def integration_error_handler(request: Request, exc: IntegrationError):
    """Handle external integration errors."""
    logger.error(f"Integration error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Integration Error",
            "detail": "External service integration failed",
            "code": "INTEGRATION_ERROR",
            "timestamp": utcnow().isoformat(),
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
        }
    )


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(request: Request, exc: ConfigurationError):
    """Handle configuration errors."""
    logger.error(f"Configuration error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Configuration Error",
            "detail": "System configuration is invalid" if not settings.debug else str(exc),
            "code": "CONFIGURATION_ERROR",
            "timestamp": utcnow().isoformat(),
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
        }
    )


# Standard exceptions
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with standard format."""
    errors = []
    for error in exc.errors():
        errors.append({
            "code": error["type"].upper(),
            "message": error["msg"],
            "field": ".".join(str(loc) for loc in error["loc"][1:]) if len(error["loc"]) > 1 else None
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": "Invalid input data",
            "code": "VALIDATION_ERROR",
            "errors": errors,
            "timestamp": utcnow().isoformat(),
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError with standard format."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request",
            "detail": str(exc),
            "code": "BAD_REQUEST",
            "timestamp": utcnow().isoformat(),
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with standard format."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred" if not settings.debug else str(exc),
            "code": "INTERNAL_SERVER_ERROR",
            "timestamp": utcnow().isoformat(),
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
        }
    )


# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add request logging middleware (first, to log all requests)
app.add_middleware(RequestLoggingMiddleware)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Request-ID"],
    max_age=600,  # Cache preflight requests for 10 minutes
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version
    }


# Import and include routers
from app.routers import agents, tasks, websocket, activities, metrics, auth
from app.routers import settings as settings_router

# Authentication endpoints (public)
app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["auth"])

# Protected endpoints
app.include_router(agents.router, prefix=f"{settings.api_prefix}/agents", tags=["agents"])
app.include_router(tasks.router, prefix=f"{settings.api_prefix}/tasks", tags=["tasks"])
app.include_router(activities.router, prefix=f"{settings.api_prefix}/activities", tags=["activities"])
app.include_router(metrics.router, prefix=f"{settings.api_prefix}/metrics", tags=["metrics"])
app.include_router(settings_router.router, prefix=f"{settings.api_prefix}/settings", tags=["settings"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
