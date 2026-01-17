# Learning Letters - ABC & 123

A fun, interactive application to help kids learn their alphabet (uppercase and lowercase) and numbers (0-9). Designed for touchscreens, smart boards, tablets, and phones.

## Features

- **Character Selection**: Choose from uppercase letters (A-Z), lowercase letters (a-z), or numbers (0-9)
- **Drawing Canvas**: Touch-friendly canvas for kids to practice drawing characters
- **Tracing Mode**: Shows character outlines with numbered strokes and directional arrows - just like kindergarten workbooks!
- **Scoring System**: AI-powered scoring that evaluates drawings and provides encouraging feedback
- **Text-to-Speech**: Hear the letter name and its phonetic sound when viewing results
- **Kid-Friendly UI**: Large buttons, bright colors, and encouraging feedback designed for young learners

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Poetry** - Python dependency management
- **Pillow** - Image processing
- **scikit-image** - Image comparison and scoring

### Frontend
- **Vue.js 3** - Progressive JavaScript framework
- **Vite** - Fast build tool
- **Axios** - HTTP client

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Poetry (Python package manager)

### Backend Setup

```bash
cd backend

# Install dependencies with Poetry
poetry install

# Run the development server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:3000` and will proxy API requests to the backend at `http://localhost:8000`.

## API Endpoints

### Characters

- `GET /api/characters` - Get all available characters organized by type
- `GET /api/characters/{character}` - Get detailed info about a character including stroke paths
- `GET /api/characters/{character}/strokes` - Get just the stroke paths for tracing

### Scoring

- `POST /api/score` - Submit a drawing for scoring
  - Request body: `{ "image_data": "base64...", "character": "A" }`
  - Returns: score, stars (1-5), feedback, reference image

## Usage

1. **Select a Category**: Choose between uppercase letters, lowercase letters, or numbers
2. **Pick a Character**: Tap on any character to start learning
3. **Draw or Trace**:
   - Toggle "Show Guide" to see the tracing outline with numbered strokes and directional arrows
   - Draw the character on the canvas
4. **Submit**: Tap "Done!" to submit your drawing for scoring
5. **View Results**:
   - See your score and star rating
   - Compare your drawing with the perfect example
   - Tap "Hear it!" to hear the character spoken aloud
6. **Practice**: Try again or move on to the next character

## Project Structure

```
learning_letters/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── routers/
│   │   │   ├── characters.py    # Character data and stroke paths
│   │   │   └── scoring.py       # Drawing scoring endpoint
│   │   ├── services/
│   │   │   └── scoring.py       # Image comparison logic
│   │   └── static/
│   │       └── references/      # Reference images
│   └── pyproject.toml           # Poetry dependencies
├── frontend/
│   ├── src/
│   │   ├── App.vue              # Main app component
│   │   ├── main.js              # Entry point
│   │   ├── style.css            # Global styles
│   │   └── components/
│   │       ├── CharacterSelection.vue  # Character picker
│   │       ├── DrawingCanvas.vue       # Drawing + tracing
│   │       └── ResultsDisplay.vue      # Score + speech
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
└── README.md
```

## Scoring Algorithm

The scoring system evaluates drawings based on:
- **Coverage** (40%): How much of the reference character is covered by the drawing
- **Accuracy** (40%): How well the drawing stays within the character bounds
- **Similarity** (20%): Structural similarity to the reference

Scores are adjusted to be encouraging for young learners while still rewarding improvement.

## License

MIT
