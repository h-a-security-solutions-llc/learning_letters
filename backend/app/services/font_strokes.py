"""
Font Strokes Service

Loads font-specific stroke definitions from JSON files for step-by-step guided drawing.
Each font has its own stroke paths that match its visual appearance.
"""

import json
import os
from typing import Any, Dict, List, Optional

# Directory containing stroke JSON files
STROKES_DIR = os.path.join(os.path.dirname(__file__), "..", "fonts", "strokes")

# Default font to use if requested font is not found
DEFAULT_FONT = "fredoka"

# Mapping of font display names to JSON file names (without extension)
FONT_NAME_MAP = {
    "Fredoka-Regular": "fredoka",
    "PlaywriteUS-Regular": "playwrite-us",
    "Nunito-Regular": "nunito",
    "PatrickHand-Regular": "patrick-hand",
    "Schoolbell-Regular": "schoolbell",
}

# Font metadata for UI display
FONT_METADATA = {
    "fredoka": {
        "display_name": "Fredoka",
        "style": "Rounded Playful",
        "description": 'Bubbly round letters with a playful feel. Number "1" has a base.',
        "characteristics": ["rounded", "playful", "kid-friendly"],
    },
    "playwrite-us": {
        "display_name": "Playwrite US",
        "style": "Educational Manuscript",
        "description": "Designed for US handwriting education with clean, teachable strokes.",
        "characteristics": ["educational", "manuscript", "clean"],
    },
    "nunito": {
        "display_name": "Nunito",
        "style": "Clean Sans-serif",
        "description": 'Simple geometric shapes. Number "1" is a straight line without base.',
        "characteristics": ["geometric", "simple", "modern"],
    },
    "patrick-hand": {
        "display_name": "Patrick Hand",
        "style": "Casual Handwriting",
        "description": "Natural pen strokes with a casual, handwritten feel.",
        "characteristics": ["casual", "handwritten", "natural"],
    },
    "schoolbell": {
        "display_name": "Schoolbell",
        "style": "Playful Handwriting",
        "description": "Kid-friendly handwriting style with a slightly bouncy baseline.",
        "characteristics": ["playful", "bouncy", "fun"],
    },
}

# In-memory cache for loaded stroke data
_stroke_cache: Dict[str, Dict[str, Any]] = {}


def get_font_key(font_name: Optional[str]) -> str:
    """
    Convert a font name (e.g., 'Fredoka-Regular') to the JSON file key (e.g., 'fredoka').
    Returns default font key if font_name is None or not found.
    """
    if not font_name:
        return DEFAULT_FONT

    # Check if it's already a key
    if font_name.lower() in FONT_METADATA:
        return font_name.lower()

    # Look up in the mapping
    return FONT_NAME_MAP.get(font_name, DEFAULT_FONT)


def get_stroke_file_path(font_key: str) -> str:
    """Get the full path to a font's stroke JSON file."""
    return os.path.join(STROKES_DIR, f"{font_key}.json")


def load_strokes(font_key: str) -> Optional[Dict[str, Any]]:
    """
    Load stroke data from a JSON file.
    Returns None if the file doesn't exist or is invalid.
    """
    # Check cache first
    if font_key in _stroke_cache:
        return _stroke_cache[font_key]

    file_path = get_stroke_file_path(font_key)

    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate basic structure
        if not isinstance(data, dict) or "characters" not in data:
            print(f"Warning: Invalid stroke file format for {font_key}")
            return None

        # Cache the data
        _stroke_cache[font_key] = data
        return data

    except json.JSONDecodeError as e:
        print(f"Error parsing stroke file for {font_key}: {e}")
        return None
    except Exception as e:
        print(f"Error loading stroke file for {font_key}: {e}")
        return None


def get_character_strokes(character: str, font_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get stroke data for a specific character in a specific font.
    Falls back to default font if requested font is not available.

    Returns:
        Dict with 'type', 'phonetic', 'sound', and 'strokes' for the character,
        or None if character is not found.
    """
    font_key = get_font_key(font_name)
    data = load_strokes(font_key)

    # Try fallback to default if requested font not found
    if data is None and font_key != DEFAULT_FONT:
        print(f"Font {font_key} not found, falling back to {DEFAULT_FONT}")
        font_key = DEFAULT_FONT
        data = load_strokes(font_key)

    if data is None:
        return None

    characters = data.get("characters", {})
    return characters.get(character)


def get_all_characters(font_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get all character data for a specific font.
    Falls back to default font if requested font is not available.
    """
    font_key = get_font_key(font_name)
    data = load_strokes(font_key)

    # Try fallback to default if requested font not found
    if data is None and font_key != DEFAULT_FONT:
        font_key = DEFAULT_FONT
        data = load_strokes(font_key)

    if data is None:
        return {}

    return data.get("characters", {})


def get_available_fonts() -> List[Dict[str, Any]]:
    """
    Get list of available fonts with their metadata.
    Only returns fonts that have stroke JSON files.
    """
    available = []

    for font_key, metadata in FONT_METADATA.items():
        file_path = get_stroke_file_path(font_key)
        if os.path.exists(file_path):
            display_name = str(metadata["display_name"])
            available.append({"key": font_key, "file_name": f"{display_name.replace(' ', '')}-Regular", **metadata})

    return available


def get_font_metadata(font_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get metadata for a specific font."""
    font_key = get_font_key(font_name)
    return FONT_METADATA.get(font_key)


def validate_stroke_format(stroke: Dict[str, Any]) -> bool:
    """
    Validate that a stroke has the required format.

    Expected format:
    {
        "points": [[x1, y1], [x2, y2], ...],
        "direction": "down" | "up" | "curve-left" | etc.
    }
    """
    if not isinstance(stroke, dict):
        return False

    if "points" not in stroke or "direction" not in stroke:
        return False

    points = stroke["points"]
    if not isinstance(points, list) or len(points) < 2:
        return False

    for point in points:
        if not isinstance(point, list) or len(point) != 2:
            return False
        if not all(isinstance(coord, (int, float)) for coord in point):
            return False

    return True


def validate_character_format(char_data: Dict[str, Any]) -> bool:
    """
    Validate that character data has the required format.

    Expected format:
    {
        "type": "uppercase" | "lowercase" | "number",
        "phonetic": "...",
        "sound": "...",
        "strokes": [...]
    }
    """
    required_fields = ["type", "phonetic", "sound", "strokes"]

    if not all(field in char_data for field in required_fields):
        return False

    if char_data["type"] not in ["uppercase", "lowercase", "number"]:
        return False

    strokes = char_data["strokes"]
    if not isinstance(strokes, list) or len(strokes) == 0:
        return False

    return all(validate_stroke_format(stroke) for stroke in strokes)


def clear_cache():
    """Clear the stroke data cache."""
    global _stroke_cache
    _stroke_cache = {}


def preload_all_fonts():
    """Preload all available font stroke data into cache."""
    for font_key in FONT_METADATA:
        load_strokes(font_key)
