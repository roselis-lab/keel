import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from keel.database import async_session
from keel.routes.library import router as library_router
from keel.services.style_guide_service import sync_skeletons

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("keel")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Sync style guide skeletons on startup. Schema is managed by Alembic —
    run `alembic upgrade head` before first launch."""
    async with async_session() as session:
        await sync_skeletons(session)
    yield


app = FastAPI(
    title="Keel",
    description="Read-only browse API for the Keel threat model. Writes go through MCP.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(library_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


# Minimal browse-and-edit UI (single static file) served at the root.
# Mounted last so the API routes and /docs take precedence over the static catch-all.
app.mount(
    "/",
    StaticFiles(directory=Path(__file__).parent / "static", html=True),
    name="ui",
)
