"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import db
from app.routes import admin, events, health

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan handler for startup and shutdown.

    Args:
        application: The FastAPI application instance.
    """
    db.initialize()
    logger.info("Application started. Database initialized.")
    yield
    db.close()
    logger.info("Application shutdown.")


app = FastAPI(
    title="NetworkX Event Discovery API",
    description="Backend API for the NetworkX global event discovery platform.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(events.router)
app.include_router(admin.router)
