from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.db.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""

    yield
    await engine.dispose()