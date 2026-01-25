"""Tests for guide_cache service."""

import pytest

from app.services.guide_cache import (
    cache_guide,
    clear_cache,
    get_cache_stats,
    get_cached_guide,
    get_or_generate_guide,
    init_db,
)


@pytest.fixture(autouse=True)
def clean_cache():
    """Clear cache before each test."""
    clear_cache()
    yield
    clear_cache()


class TestInitDb:
    """Tests for init_db function."""

    def test_creates_database(self):
        """Should create database without error."""
        init_db()
        # If no exception, it worked

    def test_idempotent(self):
        """Should be safe to call multiple times."""
        init_db()
        init_db()
        init_db()
        # If no exception, it's idempotent


class TestCacheGuide:
    """Tests for cache_guide function."""

    def test_caches_guide(self):
        """Should cache guide data."""
        guide_data = {
            "character": "A",
            "size": 400,
            "trace_image": "data:image/png;base64,abc",
            "animated_strokes": [],
            "stroke_count": 3,
            "font_name": "Fredoka-Regular",
        }
        cache_guide("A", guide_data)

        # Should be retrievable
        cached = get_cached_guide("A", 400, "Fredoka-Regular")
        assert cached is not None
        assert cached["character"] == "A"


class TestGetCachedGuide:
    """Tests for get_cached_guide function."""

    def test_returns_none_for_uncached(self):
        """Should return None for uncached character."""
        result = get_cached_guide("Z", 400)
        assert result is None

    def test_returns_cached_data(self):
        """Should return cached data."""
        guide_data = {
            "character": "B",
            "size": 400,
            "trace_image": "data:image/png;base64,xyz",
            "animated_strokes": [{"points": [[0, 0]], "color": "#FF0000", "order": 1}],
            "stroke_count": 1,
            "font_name": "Fredoka-Regular",
        }
        cache_guide("B", guide_data)

        cached = get_cached_guide("B", 400, "Fredoka-Regular")
        assert cached is not None
        assert cached["trace_image"] == "data:image/png;base64,xyz"
        assert len(cached["animated_strokes"]) == 1

    def test_respects_size(self):
        """Should respect size parameter."""
        guide_data = {
            "character": "C",
            "size": 400,
            "trace_image": "data:image/png;base64,400",
            "animated_strokes": [],
            "stroke_count": 1,
            "font_name": "Fredoka-Regular",
        }
        cache_guide("C", guide_data)

        # Different size should not match
        cached = get_cached_guide("C", 600, "Fredoka-Regular")
        assert cached is None

        # Same size should match
        cached = get_cached_guide("C", 400, "Fredoka-Regular")
        assert cached is not None

    def test_respects_font(self):
        """Should respect font_name parameter."""
        guide_data = {
            "character": "D",
            "size": 400,
            "trace_image": "data:image/png;base64,d",
            "animated_strokes": [],
            "stroke_count": 2,
            "font_name": "Nunito-Regular",
        }
        cache_guide("D", guide_data)

        # Different font should not match
        cached = get_cached_guide("D", 400, "Fredoka-Regular")
        assert cached is None

        # Same font should match
        cached = get_cached_guide("D", 400, "Nunito-Regular")
        assert cached is not None


class TestGetOrGenerateGuide:
    """Tests for get_or_generate_guide function."""

    def test_generates_when_not_cached(self):
        """Should generate guide when not cached."""
        result = get_or_generate_guide("E", 400)
        assert result is not None
        assert "character" in result
        assert "trace_image" in result

    def test_caches_generated_guide(self):
        """Should cache generated guide."""
        # Generate
        get_or_generate_guide("F", 400)

        # Should now be cached
        cached = get_cached_guide("F", 400)
        assert cached is not None

    def test_returns_cached_when_available(self):
        """Should return cached data when available."""
        # Pre-cache
        guide_data = {
            "character": "G",
            "size": 400,
            "trace_image": "data:image/png;base64,cached",
            "animated_strokes": [],
            "stroke_count": 1,
            "font_name": "Fredoka-Regular",
        }
        cache_guide("G", guide_data)

        # Should return cached version
        result = get_or_generate_guide("G", 400, "Fredoka-Regular")
        assert result["trace_image"] == "data:image/png;base64,cached"


class TestClearCache:
    """Tests for clear_cache function."""

    def test_clears_all_cached(self):
        """Should clear all cached guides."""
        # Cache some guides
        for char in ["H", "I", "J"]:
            guide_data = {
                "character": char,
                "size": 400,
                "trace_image": f"data:image/png;base64,{char}",
                "animated_strokes": [],
                "stroke_count": 1,
                "font_name": "Fredoka-Regular",
            }
            cache_guide(char, guide_data)

        # Clear
        clear_cache()

        # Should all be gone
        for char in ["H", "I", "J"]:
            assert get_cached_guide(char, 400) is None


class TestGetCacheStats:
    """Tests for get_cache_stats function."""

    def test_returns_dict(self):
        """Should return a dictionary."""
        result = get_cache_stats()
        assert isinstance(result, dict)

    def test_has_required_fields(self):
        """Should have required fields."""
        result = get_cache_stats()
        assert "cached_count" in result
        assert "fonts_cached" in result
        assert "by_font" in result

    def test_counts_cached(self):
        """Should count cached guides."""
        # Start fresh
        clear_cache()
        stats = get_cache_stats()
        assert stats["cached_count"] == 0

        # Add some
        for char in ["K", "L"]:
            guide_data = {
                "character": char,
                "size": 400,
                "trace_image": f"data:image/png;base64,{char}",
                "animated_strokes": [],
                "stroke_count": 1,
                "font_name": "Fredoka-Regular",
            }
            cache_guide(char, guide_data)

        stats = get_cache_stats()
        assert stats["cached_count"] == 2

    def test_groups_by_font(self):
        """Should group counts by font."""
        clear_cache()

        # Add for different fonts
        for font in ["Fredoka-Regular", "Nunito-Regular"]:
            guide_data = {
                "character": "M",
                "size": 400,
                "trace_image": "data:image/png;base64,m",
                "animated_strokes": [],
                "stroke_count": 2,
                "font_name": font,
            }
            cache_guide("M", guide_data)

        stats = get_cache_stats()
        assert len(stats["fonts_cached"]) == 2
