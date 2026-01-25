"""Tests for API routers."""

import base64
import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_200(self):
        """Should return 200 status."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_message(self):
        """Should return expected message."""
        response = client.get("/")
        data = response.json()
        assert "message" in data
        assert "Learning Letters" in data["message"]


class TestHealthEndpoint:
    """Tests for health endpoint."""

    def test_health_returns_200(self):
        """Should return 200 status."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy(self):
        """Should return healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"


class TestCharactersEndpoint:
    """Tests for /api/characters endpoint."""

    def test_get_all_characters(self):
        """Should return all characters."""
        response = client.get("/api/characters")
        assert response.status_code == 200
        data = response.json()
        assert "uppercase" in data
        assert "lowercase" in data
        assert "numbers" in data

    def test_uppercase_count(self):
        """Should have 26 uppercase letters."""
        response = client.get("/api/characters")
        data = response.json()
        assert len(data["uppercase"]) == 26

    def test_lowercase_count(self):
        """Should have 26 lowercase letters."""
        response = client.get("/api/characters")
        data = response.json()
        assert len(data["lowercase"]) == 26

    def test_numbers_count(self):
        """Should have 10 numbers."""
        response = client.get("/api/characters")
        data = response.json()
        assert len(data["numbers"]) == 10


class TestCharacterEndpoint:
    """Tests for /api/characters/{character} endpoint."""

    def test_get_uppercase_a(self):
        """Should return data for uppercase A."""
        response = client.get("/api/characters/A")
        assert response.status_code == 200
        data = response.json()
        assert data["character"] == "A"
        assert data["type"] == "uppercase"
        assert "strokes" in data

    def test_get_lowercase_a(self):
        """Should return data for lowercase a."""
        response = client.get("/api/characters/a")
        assert response.status_code == 200
        data = response.json()
        assert data["character"] == "a"
        assert data["type"] == "lowercase"

    def test_get_number(self):
        """Should return data for number."""
        response = client.get("/api/characters/5")
        assert response.status_code == 200
        data = response.json()
        assert data["character"] == "5"
        assert data["type"] == "number"

    def test_unknown_character(self):
        """Should return error for unknown character."""
        response = client.get("/api/characters/@")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data


class TestCharacterStrokesEndpoint:
    """Tests for /api/characters/{character}/strokes endpoint."""

    def test_get_strokes(self):
        """Should return stroke data."""
        response = client.get("/api/characters/A/strokes")
        assert response.status_code == 200
        data = response.json()
        assert "strokes" in data
        assert len(data["strokes"]) > 0

    def test_strokes_have_points(self):
        """Each stroke should have points."""
        response = client.get("/api/characters/A/strokes")
        data = response.json()
        for stroke in data["strokes"]:
            assert "points" in stroke
            assert len(stroke["points"]) >= 2

    def test_strokes_with_font(self):
        """Should accept font parameter."""
        response = client.get("/api/characters/A/strokes?font=Fredoka-Regular")
        assert response.status_code == 200


class TestCharacterGuidesEndpoint:
    """Tests for /api/characters/{character}/guides endpoint."""

    def test_get_guides(self):
        """Should return guide data."""
        response = client.get("/api/characters/A/guides")
        assert response.status_code == 200
        data = response.json()
        assert "trace_image" in data
        assert "animated_strokes" in data

    def test_trace_image_is_base64(self):
        """Trace image should be base64 data URL."""
        response = client.get("/api/characters/A/guides")
        data = response.json()
        assert data["trace_image"].startswith("data:image/png;base64,")


class TestGuidedStrokesEndpoint:
    """Tests for /api/characters/{character}/guided-strokes endpoint."""

    def test_get_guided_strokes(self):
        """Should return guided stroke data."""
        response = client.get("/api/characters/A/guided-strokes")
        assert response.status_code == 200
        data = response.json()
        assert "strokes" in data
        assert "total_strokes" in data

    def test_guided_strokes_have_zones(self):
        """Each stroke should have start and end zones."""
        response = client.get("/api/characters/A/guided-strokes")
        data = response.json()
        for stroke in data["strokes"]:
            assert "start_zone" in stroke
            assert "end_zone" in stroke
            assert "x" in stroke["start_zone"]
            assert "y" in stroke["start_zone"]
            assert "radius" in stroke["start_zone"]

    def test_guided_strokes_have_instructions(self):
        """Each stroke should have instruction."""
        response = client.get("/api/characters/A/guided-strokes")
        data = response.json()
        for stroke in data["strokes"]:
            assert "instruction" in stroke


class TestValidateStrokeEndpoint:
    """Tests for /api/characters/{character}/validate-stroke endpoint."""

    def test_validate_stroke(self):
        """Should validate stroke."""
        request_data = {
            "stroke_index": 0,
            "drawn_points": [[50, 15], [45, 30], [40, 50], [30, 70], [20, 85]],
        }
        response = client.post("/api/characters/A/validate-stroke", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "feedback" in data

    def test_validate_stroke_returns_accuracy(self):
        """Should return path accuracy."""
        request_data = {
            "stroke_index": 0,
            "drawn_points": [[50, 15], [40, 50], [20, 85]],
        }
        response = client.post("/api/characters/A/validate-stroke", json=request_data)
        data = response.json()
        assert "path_accuracy" in data

    def test_invalid_stroke_index(self):
        """Should return error for invalid stroke index."""
        request_data = {"stroke_index": 100, "drawn_points": [[0, 0], [100, 100]]}
        response = client.post("/api/characters/A/validate-stroke", json=request_data)
        data = response.json()
        assert "error" in data

    def test_too_short_stroke(self):
        """Should handle too-short stroke."""
        request_data = {"stroke_index": 0, "drawn_points": [[0, 0]]}
        response = client.post("/api/characters/A/validate-stroke", json=request_data)
        data = response.json()
        assert data["valid"] is False


class TestFontsEndpoint:
    """Tests for /api/fonts endpoint."""

    def test_get_fonts(self):
        """Should return list of fonts."""
        response = client.get("/api/fonts")
        assert response.status_code == 200
        data = response.json()
        assert "fonts" in data
        assert len(data["fonts"]) > 0

    def test_fonts_have_metadata(self):
        """Should include font metadata."""
        response = client.get("/api/fonts")
        data = response.json()
        assert "fonts_detailed" in data
        for font in data["fonts_detailed"]:
            assert "name" in font


class TestScoreEndpoint:
    """Tests for /api/score endpoint."""

    def _create_test_image_data(self) -> str:
        """Create a test image as base64 data URL."""
        img = Image.new("L", (200, 200), color=255)
        # Draw a simple shape
        for x in range(50, 150):
            for y in range(90, 110):
                img.putpixel((x, y), 0)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{base64_data}"

    def test_score_returns_200(self):
        """Should return 200 for valid request."""
        request_data = {"image_data": self._create_test_image_data(), "character": "A"}
        response = client.post("/api/score", json=request_data)
        assert response.status_code == 200

    def test_score_returns_score(self):
        """Should return score."""
        request_data = {"image_data": self._create_test_image_data(), "character": "A"}
        response = client.post("/api/score", json=request_data)
        data = response.json()
        assert "score" in data
        assert 0 <= data["score"] <= 100

    def test_score_returns_stars(self):
        """Should return stars."""
        request_data = {"image_data": self._create_test_image_data(), "character": "A"}
        response = client.post("/api/score", json=request_data)
        data = response.json()
        assert "stars" in data
        assert 1 <= data["stars"] <= 5

    def test_score_returns_feedback(self):
        """Should return feedback."""
        request_data = {"image_data": self._create_test_image_data(), "character": "A"}
        response = client.post("/api/score", json=request_data)
        data = response.json()
        assert "feedback" in data

    def test_score_missing_image(self):
        """Should return error for missing image."""
        request_data = {"image_data": "", "character": "A"}
        response = client.post("/api/score", json=request_data)
        assert response.status_code == 400

    def test_score_invalid_character(self):
        """Should return error for invalid character."""
        request_data = {"image_data": self._create_test_image_data(), "character": ""}
        response = client.post("/api/score", json=request_data)
        assert response.status_code == 400

    def test_score_with_font(self):
        """Should accept font parameter."""
        request_data = {
            "image_data": self._create_test_image_data(),
            "character": "A",
            "font": "Fredoka-Regular",
        }
        response = client.post("/api/score", json=request_data)
        assert response.status_code == 200


class TestGuideCacheEndpoints:
    """Tests for guide cache endpoints."""

    def test_get_cache_stats(self):
        """Should return cache stats."""
        response = client.get("/api/guides/stats")
        assert response.status_code == 200
        data = response.json()
        assert "cached_count" in data

    def test_clear_cache(self):
        """Should clear cache."""
        response = client.delete("/api/guides/cache")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
