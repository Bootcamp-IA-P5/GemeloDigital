# ──────────────────────────────────────────────────────────────
# 📌 IMPORTS
# ──────────────────────────────────────────────────────────────
from contextlib import asynccontextmanager  # Manage app lifecycle (startup/shutdown)

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    status,
)  # Web framework + Request object + HTTP codes
from fastapi.middleware.cors import (
    CORSMiddleware,
)  # Middleware to allow cross-origin requests (frontend)
from fastapi.responses import JSONResponse  # Build custom JSON responses

# ──────────────────────────────────────────────────────────────
# 📌 ROUTER IMPORTS (endpoints organized by domain)
# ──────────────────────────────────────────────────────────────
from app.api.routes import auth, profile, roadmap, admin
from app.api.routes.internal import router as internal_router


# ──────────────────────────────────────────────────────────────
# 📌 LIFESPAN — Application lifecycle
# ──────────────────────────────────────────────────────────────
# FastAPI uses "lifespan" to run code on startup and shutdown.
# This is where you'll connect the database, load the ML model,
# or initialize the ChromaDB client in the future.
# ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP: runs ONCE when the server starts ──
    print("🚀 Server starting...")
    # TODO: Connect to PostgreSQL
    # TODO: Load ML model (joblib.load)
    # TODO: Initialize ChromaDB client

    yield  # ← The app runs between startup and shutdown

    # ── SHUTDOWN: runs when the server stops ──
    print("🛑 Server shutting down...")
    # TODO: Close DB connections
    # TODO: Release resources


# ──────────────────────────────────────────────────────────────
# 📌 FASTAPI INSTANCE
# ──────────────────────────────────────────────────────────────
# Creates the application. Parameters define the metadata
# shown in the auto-generated Swagger docs (at /docs).
# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Gemelo Cognitivo API",  # Name shown in Swagger UI
    description=(
        "REST API for the Cognitive Twin Learning System. "
        "Orchestrates three LLM agents (Profiling, Planning, Explanatory), "
        "a RAG pipeline with ChromaDB, and an ML trajectory classification model."
    ),
    version="0.1.0",  # MVP version
    lifespan=lifespan,  # Register startup/shutdown events
)


# ──────────────────────────────────────────────────────────────
# 📌 MIDDLEWARE — CORS (Cross-Origin Resource Sharing)
# ──────────────────────────────────────────────────────────────
# The frontend (React on another port/domain) needs permission
# to make HTTP requests to this API. Without CORS, the browser
# blocks requests for security.
#
# ⚠️  In production, replace allow_origins=["*"] with the
#     actual frontend URL (e.g. ["https://my-app.vercel.app"]).
# ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allowed origins ("*" = all, dev only)
    allow_credentials=True,  # Allow cookies/tokens in requests
    allow_methods=["*"],  # Allowed HTTP methods (GET, POST, PATCH, DELETE, etc.)
    allow_headers=["*"],  # Allowed headers (Authorization, Content-Type, etc.)
)


# ──────────────────────────────────────────────────────────────
# 📌 GLOBAL EXCEPTION HANDLER
# ──────────────────────────────────────────────────────────────
# Catches ANY unhandled exception and returns a clean JSON
# instead of a generic 500 server error. This ensures the
# frontend always receives parseable responses.
# ──────────────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ──────────────────────────────────────────────────────────────
# 📌 ROUTER REGISTRATION
# ──────────────────────────────────────────────────────────────
# Each router groups endpoints for a domain. FastAPI mounts them
# under a URL prefix and assigns tags for organized Swagger docs.
# ──────────────────────────────────────────────────────────────
app.include_router(
    auth.router,
    prefix="/auth",  # All auth.py routes start with /auth/...
    tags=["Authentication"],  # Swagger UI group
)

app.include_router(
    profile.router,
    prefix="/api/profile",  # Profile routes under /api/profile/...
    tags=["Profile"],
)

app.include_router(
    roadmap.router,
    prefix="/api/roadmap",  # Roadmap routes under /api/roadmap/...
    tags=["Roadmap"],
)

app.include_router(
    admin.router,
    prefix="/api/admin",  # Admin routes under /api/admin/...
    tags=["Administration"],
)

# ── ML/IA internal endpoints (predict-path, reindex) ──
app.include_router(
    internal_router,
    prefix="/api/internal",
    tags=["Internal — ML/IA"],
)


# ──────────────────────────────────────────────────────────────
# 📌 HEALTH CHECK — Root route
# ──────────────────────────────────────────────────────────────
# Minimal endpoint to verify the API is alive.
# Useful for:
#   - Health monitoring on Railway/Render
#   - Quick verification during development
#   - Load balancers checking if the service responds
# ──────────────────────────────────────────────────────────────
@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
    response_model=dict,
)
async def health_check():
    """Return the API status."""
    return {
        "status": "ok",
        "app": "Gemelo Cognitivo API",
        "version": "0.1.0",
    }
