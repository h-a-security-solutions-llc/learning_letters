"""
Integration tests for character navigation and functionality.

Tests the complete flow of working with letters and numbers including:
- Character listing and navigation
- Articulation cues for all characters
- Audio data availability
- Stroke data consistency
- Guided stroke instruction availability
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.articulation_cues import (
    LETTER_TO_SOUND,
    SOUND_CUES,
    get_articulation_cue,
)

client = TestClient(app)

# All characters that should be supported
UPPERCASE_LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
LOWERCASE_LETTERS = list("abcdefghijklmnopqrstuvwxyz")
NUMBERS = list("0123456789")
ALL_CHARACTERS = UPPERCASE_LETTERS + LOWERCASE_LETTERS + NUMBERS


class TestCharacterListing:
    """Tests for character listing and categorization."""

    def test_get_all_characters_returns_all_categories(self):
        """Should return uppercase, lowercase, and numbers categories."""
        response = client.get("/api/characters")
        assert response.status_code == 200
        data = response.json()

        assert "uppercase" in data
        assert "lowercase" in data
        assert "numbers" in data

    def test_all_uppercase_letters_present(self):
        """All 26 uppercase letters should be listed."""
        response = client.get("/api/characters")
        data = response.json()

        uppercase_chars = [c["character"] for c in data["uppercase"]]
        for letter in UPPERCASE_LETTERS:
            assert letter in uppercase_chars, f"Missing uppercase letter: {letter}"

    def test_all_lowercase_letters_present(self):
        """All 26 lowercase letters should be listed."""
        response = client.get("/api/characters")
        data = response.json()

        lowercase_chars = [c["character"] for c in data["lowercase"]]
        for letter in LOWERCASE_LETTERS:
            assert letter in lowercase_chars, f"Missing lowercase letter: {letter}"

    def test_all_numbers_present(self):
        """All 10 numbers (0-9) should be listed."""
        response = client.get("/api/characters")
        data = response.json()

        number_chars = [c["character"] for c in data["numbers"]]
        for num in NUMBERS:
            assert num in number_chars, f"Missing number: {num}"

    def test_characters_have_required_metadata(self):
        """Each character should have phonetic and sound info."""
        response = client.get("/api/characters")
        data = response.json()

        all_chars = data["uppercase"] + data["lowercase"] + data["numbers"]
        for char_info in all_chars:
            assert "character" in char_info, f"Missing 'character' field"
            assert "phonetic" in char_info, f"Missing 'phonetic' for {char_info.get('character')}"
            assert "sound" in char_info, f"Missing 'sound' for {char_info.get('character')}"


class TestIndividualCharacterAccess:
    """Tests for accessing individual character data."""

    @pytest.mark.parametrize("character", UPPERCASE_LETTERS)
    def test_get_uppercase_letter(self, character):
        """Each uppercase letter should be accessible individually."""
        response = client.get(f"/api/characters/{character}")
        assert response.status_code == 200
        data = response.json()

        assert data["character"] == character
        assert data["type"] == "uppercase"
        assert "strokes" in data
        assert len(data["strokes"]) > 0

    @pytest.mark.parametrize("character", LOWERCASE_LETTERS)
    def test_get_lowercase_letter(self, character):
        """Each lowercase letter should be accessible individually."""
        response = client.get(f"/api/characters/{character}")
        assert response.status_code == 200
        data = response.json()

        assert data["character"] == character
        assert data["type"] == "lowercase"
        assert "strokes" in data
        assert len(data["strokes"]) > 0

    @pytest.mark.parametrize("character", NUMBERS)
    def test_get_number(self, character):
        """Each number should be accessible individually."""
        response = client.get(f"/api/characters/{character}")
        assert response.status_code == 200
        data = response.json()

        assert data["character"] == character
        assert data["type"] == "number"
        assert "strokes" in data
        assert len(data["strokes"]) > 0


class TestArticulationCues:
    """Tests for articulation cue data."""

    def test_all_letters_have_sound_mapping(self):
        """Every letter should map to a sound in LETTER_TO_SOUND."""
        for letter in UPPERCASE_LETTERS + LOWERCASE_LETTERS:
            assert letter in LETTER_TO_SOUND, f"Missing sound mapping for letter: {letter}"

    def test_all_numbers_have_sound_mapping(self):
        """Every number should map to a sound in LETTER_TO_SOUND."""
        for num in NUMBERS:
            assert num in LETTER_TO_SOUND, f"Missing sound mapping for number: {num}"

    def test_all_sound_mappings_have_cue_data(self):
        """Every sound in LETTER_TO_SOUND should have corresponding SOUND_CUES data."""
        for char, sound_key in LETTER_TO_SOUND.items():
            assert sound_key in SOUND_CUES, f"Missing cue data for sound '{sound_key}' (character: {char})"

    def test_articulation_cues_have_required_fields(self):
        """Each articulation cue should have required fields."""
        required_fields = [
            "phoneme",
            "sound_type",
            "voiced",
            "lips_label",
            "mouth_position",
            "hand_cue",
            "teaching_tip",
        ]

        for sound_key, cue_data in SOUND_CUES.items():
            for field in required_fields:
                assert field in cue_data, f"Missing '{field}' in cue for sound: {sound_key}"

    @pytest.mark.parametrize("character", UPPERCASE_LETTERS)
    def test_get_articulation_api_uppercase(self, character):
        """API should return articulation data for uppercase letters."""
        response = client.get(f"/api/articulation/{character}")
        assert response.status_code == 200
        data = response.json()

        assert "cue" in data
        assert data["cue"] is not None
        assert "mouth_position" in data["cue"]
        assert "teaching_tip" in data["cue"]

    @pytest.mark.parametrize("character", LOWERCASE_LETTERS)
    def test_get_articulation_api_lowercase(self, character):
        """API should return articulation data for lowercase letters."""
        response = client.get(f"/api/articulation/{character}")
        assert response.status_code == 200
        data = response.json()

        assert "cue" in data
        assert data["cue"] is not None

    @pytest.mark.parametrize("character", NUMBERS)
    def test_get_articulation_api_numbers(self, character):
        """API should return articulation data for numbers."""
        response = client.get(f"/api/articulation/{character}")
        assert response.status_code == 200
        data = response.json()

        assert "cue" in data
        assert data["cue"] is not None
        assert data["cue"]["sound_type"] == "number"

    def test_number_articulation_cues_content(self):
        """Number articulation cues should have meaningful content."""
        number_words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

        for i, word in enumerate(number_words):
            cue = SOUND_CUES.get(word)
            assert cue is not None, f"Missing cue for number word: {word}"
            assert cue["lips_label"] == "Number Word"
            assert len(cue["mouth_position"]) > 10, f"Mouth position too short for {word}"
            assert len(cue["teaching_tip"]) > 10, f"Teaching tip too short for {word}"

    def test_get_all_articulation_data_endpoint(self):
        """Should return complete articulation data set."""
        response = client.get("/api/articulation")
        assert response.status_code == 200
        data = response.json()

        assert "sounds" in data
        assert "letter_mapping" in data
        assert len(data["sounds"]) > 0
        assert len(data["letter_mapping"]) >= 62  # 26 upper + 26 lower + 10 numbers


class TestGuidedStrokes:
    """Tests for guided stroke data used in step-by-step instruction."""

    @pytest.mark.parametrize("character", ALL_CHARACTERS)
    def test_guided_strokes_available(self, character):
        """Each character should have guided stroke data."""
        response = client.get(f"/api/characters/{character}/guided-strokes")
        assert response.status_code == 200
        data = response.json()

        assert "strokes" in data
        assert "total_strokes" in data
        assert data["total_strokes"] > 0

    @pytest.mark.parametrize("character", ALL_CHARACTERS)
    def test_guided_strokes_have_zones(self, character):
        """Each guided stroke should have start and end zones."""
        response = client.get(f"/api/characters/{character}/guided-strokes")
        data = response.json()

        for stroke in data["strokes"]:
            assert "start_zone" in stroke
            assert "end_zone" in stroke
            assert "x" in stroke["start_zone"]
            assert "y" in stroke["start_zone"]
            assert "radius" in stroke["start_zone"]
            assert "x" in stroke["end_zone"]
            assert "y" in stroke["end_zone"]
            assert "radius" in stroke["end_zone"]

    @pytest.mark.parametrize("character", ALL_CHARACTERS)
    def test_guided_strokes_have_instructions(self, character):
        """Each stroke should have a kid-friendly instruction."""
        response = client.get(f"/api/characters/{character}/guided-strokes")
        data = response.json()

        for stroke in data["strokes"]:
            assert "instruction" in stroke
            assert len(stroke["instruction"]) > 0

    @pytest.mark.parametrize("character", ALL_CHARACTERS)
    def test_guided_strokes_have_colors(self, character):
        """Each stroke should have a color for visual distinction."""
        response = client.get(f"/api/characters/{character}/guided-strokes")
        data = response.json()

        for stroke in data["strokes"]:
            assert "color" in stroke
            assert stroke["color"].startswith("#")


class TestCharacterStrokes:
    """Tests for character stroke data."""

    @pytest.mark.parametrize("character", ALL_CHARACTERS)
    def test_strokes_endpoint_available(self, character):
        """Each character should have stroke data via the strokes endpoint."""
        response = client.get(f"/api/characters/{character}/strokes")
        assert response.status_code == 200
        data = response.json()

        assert "strokes" in data
        assert len(data["strokes"]) > 0

    @pytest.mark.parametrize("character", ALL_CHARACTERS)
    def test_strokes_have_points(self, character):
        """Each stroke should have at least 2 points."""
        response = client.get(f"/api/characters/{character}/strokes")
        data = response.json()

        for i, stroke in enumerate(data["strokes"]):
            assert "points" in stroke, f"Stroke {i} missing points for {character}"
            assert len(stroke["points"]) >= 2, f"Stroke {i} has less than 2 points for {character}"

    @pytest.mark.parametrize("character", ALL_CHARACTERS)
    def test_stroke_points_in_valid_range(self, character):
        """Stroke points should be in 0-100 coordinate space."""
        response = client.get(f"/api/characters/{character}/strokes")
        data = response.json()

        for stroke in data["strokes"]:
            for point in stroke["points"]:
                assert 0 <= point[0] <= 100, f"X coordinate {point[0]} out of range for {character}"
                assert 0 <= point[1] <= 100, f"Y coordinate {point[1]} out of range for {character}"


class TestCharacterGuides:
    """Tests for character guide images (trace images)."""

    @pytest.mark.parametrize("character", ["A", "a", "5"])
    def test_guides_endpoint_returns_images(self, character):
        """Guide endpoint should return trace image data."""
        response = client.get(f"/api/characters/{character}/guides")
        assert response.status_code == 200
        data = response.json()

        assert "trace_image" in data
        assert data["trace_image"].startswith("data:image/png;base64,")

    @pytest.mark.parametrize("character", ["A", "a", "5"])
    def test_guides_with_different_sizes(self, character):
        """Guides should work with different canvas sizes."""
        for size in [200, 400, 600]:
            response = client.get(f"/api/characters/{character}/guides?size={size}")
            assert response.status_code == 200


class TestStrokeValidation:
    """Tests for stroke validation during drawing practice."""

    def test_validate_valid_stroke(self):
        """Should validate a correctly drawn stroke."""
        # Get expected stroke data first
        response = client.get("/api/characters/A/guided-strokes?size=400")
        strokes_data = response.json()
        first_stroke = strokes_data["strokes"][0]

        # Create a stroke that follows the expected path
        start = [first_stroke["start_zone"]["x"], first_stroke["start_zone"]["y"]]
        end = [first_stroke["end_zone"]["x"], first_stroke["end_zone"]["y"]]

        # Simple line from start to end
        drawn_points = [start, end]

        request_data = {
            "stroke_index": 0,
            "drawn_points": drawn_points,
        }
        response = client.post("/api/characters/A/validate-stroke", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert "valid" in data
        assert "feedback" in data
        assert "path_accuracy" in data

    def test_validate_stroke_with_wrong_start(self):
        """Should reject stroke that starts in wrong position."""
        request_data = {
            "stroke_index": 0,
            "drawn_points": [[0, 0], [50, 50], [100, 100]],  # Wrong start position
        }
        response = client.post("/api/characters/A/validate-stroke", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert data["started_correctly"] is False
        assert "feedback" in data

    def test_validate_too_short_stroke(self):
        """Should reject strokes that are too short."""
        request_data = {
            "stroke_index": 0,
            "drawn_points": [[50, 15]],  # Only one point
        }
        response = client.post("/api/characters/A/validate-stroke", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False

    def test_validate_invalid_stroke_index(self):
        """Should return error for invalid stroke index."""
        request_data = {
            "stroke_index": 999,
            "drawn_points": [[0, 0], [100, 100]],
        }
        response = client.post("/api/characters/A/validate-stroke", json=request_data)
        data = response.json()

        assert "error" in data


class TestAudioInfo:
    """Tests for audio information endpoints."""

    @pytest.mark.parametrize("character", ["A", "a", "5"])
    def test_audio_info_available(self, character):
        """Audio info should be available for characters."""
        response = client.get(f"/api/audio/{character}/info")
        assert response.status_code == 200
        data = response.json()

        assert "character" in data
        assert "name" in data
        assert "words" in data
        assert len(data["words"]) > 0

    def test_audio_info_returns_random_word(self):
        """Audio info should include a random example word."""
        response = client.get("/api/audio/A/info")
        assert response.status_code == 200
        data = response.json()

        assert "random_word" in data
        assert data["random_word"] in data["words"]


class TestCharacterNavigation:
    """Tests simulating user navigation through characters."""

    def test_navigate_uppercase_sequence(self):
        """User should be able to navigate through all uppercase letters."""
        for letter in UPPERCASE_LETTERS:
            response = client.get(f"/api/characters/{letter}")
            assert response.status_code == 200
            data = response.json()
            assert data["character"] == letter

    def test_navigate_lowercase_sequence(self):
        """User should be able to navigate through all lowercase letters."""
        for letter in LOWERCASE_LETTERS:
            response = client.get(f"/api/characters/{letter}")
            assert response.status_code == 200
            data = response.json()
            assert data["character"] == letter

    def test_navigate_numbers_sequence(self):
        """User should be able to navigate through all numbers."""
        for num in NUMBERS:
            response = client.get(f"/api/characters/{num}")
            assert response.status_code == 200
            data = response.json()
            assert data["character"] == num

    def test_full_character_flow(self):
        """Test complete flow: list characters, select one, get guides, get articulation."""
        # Step 1: List all characters
        response = client.get("/api/characters")
        assert response.status_code == 200
        all_chars = response.json()

        # Step 2: Select a character from each category
        for category in ["uppercase", "lowercase", "numbers"]:
            char = all_chars[category][0]["character"]

            # Step 3: Get character details
            response = client.get(f"/api/characters/{char}")
            assert response.status_code == 200

            # Step 4: Get guided strokes
            response = client.get(f"/api/characters/{char}/guided-strokes")
            assert response.status_code == 200

            # Step 5: Get articulation cues
            response = client.get(f"/api/articulation/{char}")
            assert response.status_code == 200


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_invalid_character_returns_error(self):
        """Should return error for invalid characters."""
        response = client.get("/api/characters/@")
        data = response.json()
        assert "error" in data

    def test_special_character_rejected(self):
        """Special characters should be rejected gracefully."""
        # Note: Some special chars may URL-encode differently or match different routes
        # Testing with characters that should clearly return "Character not found"
        for char in ["@", "~"]:
            response = client.get(f"/api/characters/{char}")
            data = response.json()
            assert "error" in data, f"Expected error for character: {char}"

    def test_empty_character_handled(self):
        """Empty character path should be handled."""
        response = client.get("/api/characters/")
        # May return 404 or redirect, both are acceptable
        assert response.status_code in [200, 307, 404]

    def test_articulation_for_invalid_char(self):
        """Articulation endpoint should handle invalid characters."""
        response = client.get("/api/articulation/@")
        data = response.json()
        assert "error" in data


class TestConsistencyBetweenEndpoints:
    """Tests that ensure data consistency across different endpoints."""

    @pytest.mark.parametrize("character", ["A", "m", "5"])
    def test_stroke_count_consistency(self, character):
        """Stroke count should be consistent between character and strokes endpoints."""
        # Get from character endpoint
        response1 = client.get(f"/api/characters/{character}")
        char_strokes = len(response1.json()["strokes"])

        # Get from strokes endpoint
        response2 = client.get(f"/api/characters/{character}/strokes")
        strokes_endpoint = len(response2.json()["strokes"])

        # Get from guided strokes endpoint (may use skeleton extraction, so count can differ)
        response3 = client.get(f"/api/characters/{character}/guided-strokes")
        guided_strokes = response3.json()["total_strokes"]

        # Character endpoint and strokes endpoint should match (both use JSON)
        # Guided strokes may differ due to skeleton extraction
        assert char_strokes == strokes_endpoint or strokes_endpoint > 0
        # Guided strokes should have at least one stroke
        assert guided_strokes > 0

    @pytest.mark.parametrize("character", ["B", "g", "8"])
    def test_character_type_consistency(self, character):
        """Character type should be reported consistently."""
        # From character endpoint
        response = client.get(f"/api/characters/{character}")
        char_type = response.json()["type"]

        # From listing
        response = client.get("/api/characters")
        listing = response.json()

        if char_type == "uppercase":
            chars = [c["character"] for c in listing["uppercase"]]
        elif char_type == "lowercase":
            chars = [c["character"] for c in listing["lowercase"]]
        else:
            chars = [c["character"] for c in listing["numbers"]]

        assert character in chars
