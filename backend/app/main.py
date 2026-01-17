from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.routers import scoring, characters

app = FastAPI(
    title="Learning Letters API",
    description="API for kids alphabet and number learning app",
    version="0.1.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for reference images
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include routers
app.include_router(scoring.router, prefix="/api", tags=["scoring"])
app.include_router(characters.router, prefix="/api", tags=["characters"])


@app.get("/")
async def root():
    return {"message": "Learning Letters API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
