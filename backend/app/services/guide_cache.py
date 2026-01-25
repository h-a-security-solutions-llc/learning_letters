"""Guide cache service for storing and retrieving generated character guides."""

import json
import os
import sqlite3
from typing import Optional

from app.services.trace_generator import generate_all_guides

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "guides.db")


def init_db():
    """Initialize the database and create tables if needed"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS character_guides (
            character TEXT,
            size INTEGER,
            trace_image TEXT,
            animated_strokes TEXT,
            stroke_count INTEGER,
            font_name TEXT DEFAULT 'Fredoka-Regular',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (character, size, font_name)
        )
    """
    )

    conn.commit()
    conn.close()


def get_cached_guide(character: str, size: int = 400, font_name: Optional[str] = None) -> Optional[dict]:
    """Get cached guide data for a character"""
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    font_name = font_name or "Fredoka-Regular"

    cursor.execute(
        """
        SELECT character, size, trace_image, animated_strokes, stroke_count, font_name
        FROM character_guides
        WHERE character = ? AND size = ? AND (font_name = ? OR (font_name IS NULL AND ? = 'Fredoka-Regular'))
    """,
        (character, size, font_name, font_name),
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "character": row[0],
            "size": row[1],
            "trace_image": row[2],
            "animated_strokes": json.loads(row[3]),
            "stroke_count": row[4],
            "font_name": row[5] or "Fredoka-Regular",
        }

    return None


def cache_guide(_character: str, guide_data: dict):
    """Cache guide data for a character. Character is in guide_data, param kept for API consistency."""
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    font_name = guide_data.get("font_name", "Fredoka-Regular")

    # Use a composite key of character + size + font_name
    # First delete any existing entry with same key
    cursor.execute(
        """
        DELETE FROM character_guides
        WHERE character = ? AND size = ? AND (font_name = ? OR (font_name IS NULL AND ? = 'Fredoka-Regular'))
    """,
        (guide_data["character"], guide_data["size"], font_name, font_name),
    )

    cursor.execute(
        """
        INSERT INTO character_guides
        (character, size, trace_image, animated_strokes, stroke_count, font_name)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            guide_data["character"],
            guide_data["size"],
            guide_data["trace_image"],
            json.dumps(guide_data["animated_strokes"]),
            guide_data["stroke_count"],
            font_name,
        ),
    )

    conn.commit()
    conn.close()


def get_or_generate_guide(character: str, size: int = 400, font_name: Optional[str] = None) -> dict:
    """Get guide from cache or generate and cache it"""
    # Try cache first
    cached = get_cached_guide(character, size, font_name)
    if cached:
        return cached

    # Generate new guide
    guide_data = generate_all_guides(character, size, font_name)

    # Cache it
    cache_guide(character, guide_data)

    return guide_data


def pregenerate_all_guides(size: int = 400):
    """Pre-generate guides for all characters"""
    # All uppercase letters
    uppercase = [chr(i) for i in range(ord("A"), ord("Z") + 1)]
    # All lowercase letters
    lowercase = [chr(i) for i in range(ord("a"), ord("z") + 1)]
    # Numbers 0-9
    numbers = [str(i) for i in range(10)]

    all_chars = uppercase + lowercase + numbers

    generated = 0
    for char in all_chars:
        try:
            get_or_generate_guide(char, size)
            generated += 1
            print(f"Generated guide for '{char}' ({generated}/{len(all_chars)})")
        except Exception as e:
            print(f"Failed to generate guide for '{char}': {e}")

    return generated


def clear_cache():
    """Clear all cached guides (useful when font changes)"""
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM character_guides")
    conn.commit()
    conn.close()


def get_cache_stats() -> dict:
    """Get statistics about the cache"""
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM character_guides")
    count = cursor.fetchone()[0]

    cursor.execute("SELECT DISTINCT font_name FROM character_guides")
    fonts = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT font_name, COUNT(*) FROM character_guides GROUP BY font_name")
    by_font = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return {"cached_count": count, "fonts_cached": fonts, "by_font": by_font}
