import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from keel.errors import KeelError

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

@app.exception_handler(KeelError)
async def keel_error_handler(request: Request, exc: KeelError) -> JSONResponse:
    """One translation from a service failure to a status code.

    Routes used to do this each for themselves by reading the message - literally
    `if "already has" in result["error"]` - so rewording an error changed an HTTP status
    and every new route re-derived the same mapping."""
    return JSONResponse(status_code=exc.status, content=exc.as_dict())


app.include_router(library_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


# Minimal browse-and-edit UI: one static file, no assets, no build step.
_INDEX = Path(__file__).parent / "static" / "index.html"


@app.get("/{full_path:path}", include_in_schema=False)
async def app_shell(full_path: str):
    """Serve the UI for every path the API did not claim.

    Views used to live behind a `#` because the API owned `/threats` and `/mitigations`
    at the root, so there was nowhere else for them to go. The API now sits under
    `/api`, which frees those paths: a view has a real URL that can be linked, opened
    cold, and read. Declared last, so `/api/*`, `/health` and `/docs` all match first.

    The `/api` namespace is excluded explicitly. Without that this route answers every
    unmatched API path with 200 and a page of HTML — a typo'd endpoint looks like it
    worked, and a rejected path (a traversal attempt, say) stops looking rejected.
    """
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(_INDEX)
