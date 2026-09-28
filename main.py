import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import get_settings
from app.api.router import api_router

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()
frontend_dist = Path(__file__).resolve().parent / "frontend" / "dist"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for the AI Tutor for Adaptive Programming Practice",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include main router
app.include_router(api_router, prefix="/api/v1")

if (frontend_dist / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="frontend-assets")

@app.on_event("startup")
def load_models():
    from app.ml.model_loader import ModelLoader
    ModelLoader.get_instance()

@app.get("/", tags=["Root"])
async def root():
    if (frontend_dist / "index.html").is_file():
        return FileResponse(frontend_dist / "index.html")
    return {"message": f"Welcome to the {settings.PROJECT_NAME} API"}


@app.get("/{path:path}", include_in_schema=False)
async def frontend_routes(path: str):
    if path.startswith(("api/", "docs", "redoc", "openapi.json")):
        raise HTTPException(status_code=404)
    if not (frontend_dist / "index.html").is_file():
        raise HTTPException(status_code=404)

    requested_file = (frontend_dist / path).resolve()
    try:
        requested_file.relative_to(frontend_dist.resolve())
    except ValueError:
        raise HTTPException(status_code=404)

    if requested_file.is_file():
        return FileResponse(requested_file)
    return FileResponse(frontend_dist / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
