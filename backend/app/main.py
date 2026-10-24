"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create any missing tables before the app starts serving."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Car Dealership Inventory System", lifespan=lifespan)

app.include_router(auth.router)


@app.get("/api/health", tags=["meta"])
def health() -> dict:
    """Cheap readiness probe."""
    return {"status": "ok"}
