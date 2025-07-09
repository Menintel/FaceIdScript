from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
import os
from pathlib import Path

from app.database.models import init_db
from app.config import settings
from app.api.endpoints import router as api_router

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Face Recognition API using DeepFace",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Set up templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "templates" / "static")), name="static")

# Serve captured faces
app.mount("/captured_faces", StaticFiles(directory=settings.UPLOAD_FOLDER), name="captured_faces")

# Create directories if they don't exist
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BASE_DIR / "templates" / "static", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Keep the API info endpoint for backward compatibility
@app.get("/api")
async def api_info():
    return {
        "message": "Welcome to the Face Recognition API",
        "documentation": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1
    )
