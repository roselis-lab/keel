import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from keel.routes.library import router as library_router
from keel.store import get_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("keel")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the catalog from `catalog/*.yaml` into memory on startup — no setup step."""
    store = get_store()
    logger.info(
        "Loaded catalog: %d threats, %d mitigations", len(store.threats), len(store.mitigations)
    )
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
