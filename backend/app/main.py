from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def pregenerate_audio_files():
    """Pre-generate all audio files in background thread."""
    from app.services.audio_generator import generate_audio_file, get_audio_path, CHARACTER_DATA

    # Generate for Rachel (female) and Adam (male) voices
    for voice in ['rachel', 'adam']:
        missing = 0
        generated = 0

        for character in CHARACTER_DATA.keys():
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
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Start audio pre-generation in background thread (non-blocking)
    thread = threading.Thread(target=pregenerate_audio_files, daemon=True)
    thread.start()
    yield
    # Cleanup on shutdown (if needed)


from app.routers import scoring, characters

app = FastAPI(
    title="Learning Letters API",
    description="API for kids alphabet and number learning app",
    version="0.1.0",
    lifespan=lifespan
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


def main():
    """Entry point for poetry run letters command."""
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=7000, reload=True)
