"""Main FastAPI application for Learning Letters API."""

import os
import threading
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import characters, scoring

# Load environment variables
load_dotenv()


def pregenerate_audio_files():
    """Pre-generate all audio files in background thread."""
    from app.services.audio_generator import CHARACTER_DATA, generate_audio_file, get_audio_path

    # Generate for Rachel (female) and Adam (male) voices
    for voice in ["rachel", "adam"]:
        missing = 0
        generated = 0

        for character in CHARACTER_DATA:
            path = get_audio_path(character, voice)
            if not os.path.exists(path):
                missing += 1
                try:
                    generate_audio_file(character, voice)
                    generated += 1
                    print(f"Generated {voice} audio for '{character}' ({generated} new)")
                except Exception as e:
                    print(f"Failed to generate {voice} audio for '{character}': {e}")

        if missing == 0:
            print(f"All {voice} voice audio files already exist ({len(CHARACTER_DATA)} files)")
        else:
            print(f"Generated {generated}/{missing} missing {voice} voice audio files")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup and shutdown events."""
    # Start audio pre-generation in background thread (non-blocking)
    thread = threading.Thread(target=pregenerate_audio_files, daemon=True)
    thread.start()
    yield
    # Cleanup on shutdown (if needed)


app = FastAPI(
    title="Learning Letters API",
    description="API for kids alphabet and number learning app",
    version="0.1.0",
    lifespan=lifespan,
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
    """Root endpoint returning API status."""
    return {"message": "Learning Letters API", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def main():
    """Entry point for poetry run letters command."""
    import uvicorn

    # nosec B104 - Development server binding to all interfaces for local testing
    uvicorn.run("app.main:app", host="0.0.0.0", port=7000, reload=True)  # nosec
