# Optimized static file serving for FastAPI + Next.js

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import os


def setup_optimized_static_serving(app: FastAPI, project_root: Path):
    """
    Optimized static file serving configuration for Next.js + FastAPI
    """

    # Define paths
    frontend_build_path = project_root / "frontend" / ".next" / "standalone"
    frontend_static_path = project_root / "frontend" / ".next" / "static"
    frontend_public_path = project_root / "frontend" / "public"

    # 1. Mount Next.js static files with caching headers
    if frontend_static_path.exists():
        app.mount(
            "/_next/static",
            StaticFiles(
                directory=str(frontend_static_path),
                html=False,  # Don't serve HTML from static
                check_dir=True,
            ),
            name="next_static",
        )

    # 2. Mount public assets with proper MIME types
    if frontend_public_path.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(frontend_public_path), html=False),
            name="public_assets",
        )

    # 3. Add cache headers for static assets
    @app.middleware("http")
    async def add_cache_headers(request, call_next):
        response = await call_next(request)

        # Cache static assets for longer
        if request.url.path.startswith("/_next/static"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif request.url.path.startswith("/assets"):
            response.headers["Cache-Control"] = "public, max-age=86400"

        return response

    return app


# Example usage in main.py:
# app = setup_optimized_static_serving(app, project_root)
