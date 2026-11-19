"""FastAPI application entrypoint for Clipper v2 dashboard and API."""

import os
from pathlib import Path

# Automatically load .env if present
env_file = Path(__file__).resolve().parent.parent / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.routes import config, jobs, clips, notifications, instagram

app = FastAPI(
    title="Clipper v2 API",
    description="Backend API and SPA server for AI Clipper Agent",
    version="2.0.0",
)

# CORS setup for dev server (Vite on :5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(config.router)
app.include_router(jobs.router)
app.include_router(clips.router)
app.include_router(notifications.router)
app.include_router(instagram.router)


@app.get("/healthz", tags=["health"])
def health_check():
    """Liveness probe for Render / Docker health checks."""
    return {"status": "ok", "app": "clipper-v2"}


# Public config route to provide Firebase frontend config if configured in Render env var
@app.get("/api/public-config", tags=["config"])
def get_public_config():
    """Expose non-secret public config like FIREBASE_WEB_CONFIG for frontend bootstrap."""
    import json
    cfg_str = os.environ.get("FIREBASE_WEB_CONFIG", "{}")
    try:
        cfg = json.loads(cfg_str)
    except Exception:
        cfg = {}
    return {"firebase": cfg}


# ── Mount Frontend Built SPA if available ───────────────────────────
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))

