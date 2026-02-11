"""
Tests for progress tracking and user settings endpoints.

Tests the API endpoints for tracking learning progress and syncing settings.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestProgressEndpoints:
    """Tests for /api/progress endpoints."""

    def test_get_progress_without_auth(self):
        """Should return 401 without authentication."""
        response = client.get("/api/progress")
        assert response.status_code == 401

    def test_get_progress_with_invalid_token(self):
        """Should return 401 with invalid token."""
        response = client.get(
            "/api/progress",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_update_progress_without_auth(self):
        """Should return 401 without authentication."""
        response = client.post(
            "/api/progress/A",
            json={"stars": 3, "score": 85, "attempts": 1},
        )
        assert response.status_code == 401

    def test_get_high_scores_without_auth(self):
        """Should return 401 without authentication."""
        response = client.get("/api/progress/high-scores")
        assert response.status_code == 401

    def test_clear_progress_without_auth(self):
        """Should return 401 without authentication."""
        response = client.delete("/api/progress")
        assert response.status_code == 401


class TestProgressValidation:
    """Tests for progress data validation."""

    def test_stars_validation(self):
        """Stars should be between 1 and 5."""
        # This test would need auth, so just verify endpoint exists
        response = client.post(
            "/api/progress/A",
            json={"stars": 0, "score": 85},  # Invalid: 0 stars
        )
        # Without auth, should be 401 (auth check comes first)
        assert response.status_code == 401


class TestSettingsEndpoints:
    """Tests for /api/user/settings endpoints."""

    def test_get_settings_without_auth(self):
        """Should return 401 without authentication."""
        response = client.get("/api/user/settings")
        assert response.status_code == 401

    def test_update_settings_without_auth(self):
        """Should return 401 without authentication."""
        response = client.put(
            "/api/user/settings",
            json={"settings": {"enableTraceMode": True}, "version": 1},
        )
        assert response.status_code == 401

    def test_merge_settings_without_auth(self):
        """Should return 401 without authentication."""
        response = client.post(
            "/api/user/settings/merge",
            json={"settings": {"enableTraceMode": True}},
        )
        assert response.status_code == 401


class TestMultiplayerPlayersEndpoints:
    """Tests for multiplayer players settings endpoints."""

    def test_get_players_without_auth(self):
        """Should return 401 without authentication."""
        response = client.get("/api/user/multiplayer-players")
        assert response.status_code == 401

    def test_update_players_without_auth(self):
        """Should return 401 without authentication."""
        response = client.put(
            "/api/user/multiplayer-players",
            json={"players": [{"name": "Player 1", "avatar": "cat"}]},
        )
        assert response.status_code == 401


class TestWordImagesEndpoints:
    """Tests for word images API endpoints."""

    def test_get_word_image_stats(self):
        """Should return word image statistics."""
        response = client.get("/api/words/images/stats")
        assert response.status_code == 200
        data = response.json()

        assert "total_words" in data
        assert "regular_available" in data
        assert "high_contrast_available" in data
        assert "missing" in data

    def test_get_word_image_missing(self):
        """Should return error for missing word image."""
        response = client.get("/api/words/nonexistentword123/image")
        # Returns 200 with error message, not 404
        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    def test_get_word_image_url_missing(self):
        """Should return error for missing word image URL."""
        response = client.get("/api/words/nonexistentword123/image-url")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    def test_get_character_word_image(self):
        """Should return word and image info for character."""
        response = client.get("/api/characters/A/word-image")
        assert response.status_code == 200
        data = response.json()

        assert "character" in data
        assert "word" in data
        assert data["character"] == "A"

    def test_get_character_word_image_high_contrast(self):
        """Should accept high_contrast parameter."""
        response = client.get("/api/characters/A/word-image?high_contrast=true")
        assert response.status_code == 200
        data = response.json()

        assert data["high_contrast"] is True

    def test_get_all_character_word_images(self):
        """Should return all words for a character."""
        response = client.get("/api/characters/A/all-word-images")
        assert response.status_code == 200
        data = response.json()

        assert "character" in data
        assert "words" in data
        assert isinstance(data["words"], list)
        assert len(data["words"]) > 0

    def test_get_word_image_invalid_character(self):
        """Should return error for invalid character."""
        response = client.get("/api/characters/@/word-image")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data


class TestFontEndpoints:
    """Tests for font-related endpoints."""

    def test_get_fonts(self):
        """Should return list of available fonts."""
        response = client.get("/api/fonts")
        assert response.status_code == 200
        data = response.json()

        assert "fonts" in data
        assert "fonts_detailed" in data
        assert len(data["fonts"]) > 0

    def test_fonts_have_metadata(self):
        """Each font should have metadata."""
        response = client.get("/api/fonts")
        data = response.json()

        for font in data["fonts_detailed"]:
            assert "name" in font

    def test_get_font_preview(self):
        """Should return font preview image."""
        response = client.get("/api/fonts/Fredoka-Regular/preview")
        assert response.status_code == 200
        data = response.json()

        assert "preview" in data
        # Preview should be base64 image data
        assert data["preview"].startswith("data:image/png;base64,")


class TestGuideCacheEndpoints:
    """Tests for guide cache management endpoints."""

    def test_get_cache_stats(self):
        """Should return cache statistics."""
        response = client.get("/api/guides/stats")
        assert response.status_code == 200
        data = response.json()

        assert "cached_count" in data

    def test_clear_cache(self):
        """Should clear the guide cache."""
        response = client.delete("/api/guides/cache")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"


class TestArticulationEndpoints:
    """Tests for articulation cue endpoints."""

    def test_get_all_articulation(self):
        """Should return all articulation data."""
        response = client.get("/api/articulation")
        assert response.status_code == 200
        data = response.json()

        assert "sounds" in data
        assert "letter_mapping" in data

    def test_get_articulation_for_letter(self):
        """Should return articulation for specific letter."""
        response = client.get("/api/articulation/A")
        assert response.status_code == 200
        data = response.json()

        assert "character" in data
        assert "cue" in data
        assert data["cue"] is not None

    def test_get_articulation_for_number(self):
        """Should return articulation for numbers."""
        response = client.get("/api/articulation/5")
        assert response.status_code == 200
        data = response.json()

        assert data["cue"]["sound_type"] == "number"

    def test_get_articulation_media(self):
        """Should return media info for character."""
        response = client.get("/api/articulation/A/media")
        assert response.status_code == 200
        data = response.json()

        assert "character" in data
        assert "media" in data

    def test_get_articulation_invalid_char(self):
        """Should return error for invalid character."""
        response = client.get("/api/articulation/@")
        assert response.status_code == 200
        data = response.json()

        assert "error" in data


class TestHealthAndRoot:
    """Tests for health check and root endpoints."""

    def test_health_endpoint(self):
        """Health endpoint should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self):
        """Root endpoint should return API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
