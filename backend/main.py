"""
FedCredit Score — FastAPI Application
Serves the API and static frontend files.
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.routes.upload import router as upload_router
from backend.routes.analysis import router as analysis_router
from backend.routes.history import router as history_router

# Initialize database tables
import backend.database

app = FastAPI(
    title="FedCredit Score",
    description="AI Financial Intelligence Engine — Federated Credit Scoring",
    version="1.0.0",
)

# CORS (allow all for hackathon)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(history_router)
app.include_router(upload_router)
app.include_router(analysis_router)

# Resolve frontend path
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# Serve static sub-directories
for subdir in ("css", "js", "assets"):
    static_path = FRONTEND_DIR / subdir
    if static_path.exists():
        app.mount(f"/{subdir}", StaticFiles(directory=str(static_path)), name=subdir)


@app.get("/")
async def serve_landing():
    # Start on the new landing page
    return FileResponse(str(FRONTEND_DIR / "landing.html"))


@app.get("/upload")
async def serve_upload():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"))


@app.get("/dashboard.html")
async def serve_dashboard_html():
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"))
