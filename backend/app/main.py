from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import Base, engine

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG if settings.APP_ENV == "development" else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed data
    logger.info("Starting ViralFlux API (env=%s)", settings.APP_ENV)

    # Import all models so metadata is populated
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ensured.")

    from app.seed import seed

    try:
        await seed()
    except Exception as exc:
        logger.error("Seed failed (non-fatal): %s", exc)

    yield

    # Shutdown
    await engine.dispose()
    logger.info("ViralFlux API shutdown complete.")


app = FastAPI(
    title="ViralFlux API",
    version="1.0.0",
    description="YouTube Shorts Automation SaaS — backend API",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

# CORS
allowed_origins = [
    settings.APP_URL,
    "http://localhost:3000",
    "http://localhost",
]
if settings.APP_ENV == "development":
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Resource not found."},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.exception("Unhandled server error on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error."},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


# Health check
@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": app.version, "env": settings.APP_ENV}


# Mount all v1 routes
from app.api.v1 import v1_router  # noqa: E402

app.include_router(v1_router, prefix="/api/v1")
