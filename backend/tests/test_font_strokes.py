"""Tests for font_strokes service."""

from app.services.font_strokes import (
    DEFAULT_FONT,
    FONT_NAME_MAP,
    clear_cache,
    get_all_characters,
    get_available_fonts,
    get_character_strokes,
    get_font_key,
    get_font_metadata,
    validate_character_format,
    validate_stroke_format,
)


class TestGetFontKey:
    """Tests for get_font_key function."""

    def test_returns_default_for_none(self):
        """Should return default font when font_name is None."""
        result = get_font_key(None)
        assert result == DEFAULT_FONT

    def test_returns_default_for_empty_string(self):
        """Should return default font for empty string."""
        result = get_font_key("")
        assert result == DEFAULT_FONT

    def test_returns_key_for_lowercase(self):
        """Should return font key when given lowercase key."""
        result = get_font_key("fredoka")
        assert result == "fredoka"

    def test_maps_display_name_to_key(self):
        """Should map display name to font key."""
        result = get_font_key("Fredoka-Regular")
        assert result == "fredoka"

    def test_maps_all_known_fonts(self):
        """Should correctly map all known font names."""
        for display_name, key in FONT_NAME_MAP.items():
            result = get_font_key(display_name)
            assert result == key

    def test_returns_default_for_unknown(self):
        """Should return default for unknown font name."""
        result = get_font_key("UnknownFont")
        assert result == DEFAULT_FONT


class TestGetCharacterStrokes:
    """Tests for get_character_strokes function."""

    def test_returns_data_for_uppercase_a(self):
        """Should return stroke data for uppercase A."""
        result = get_character_strokes("A")
        assert result is not None
        assert "strokes" in result
        assert "type" in result
        assert result["type"] == "uppercase"

    def test_returns_data_for_lowercase_a(self):
        """Should return stroke data for lowercase a."""
        result = get_character_strokes("a")
        assert result is not None
        assert "strokes" in result
        assert result["type"] == "lowercase"

    def test_returns_data_for_number(self):
        """Should return stroke data for number."""
        result = get_character_strokes("1")
        assert result is not None
        assert "strokes" in result
        assert result["type"] == "number"

    def test_returns_none_for_unknown_character(self):
        """Should return None for unknown character."""
        result = get_character_strokes("@")
        assert result is None

    def test_returns_data_for_specific_font(self):
        """Should return stroke data for specific font."""
        result = get_character_strokes("A", "Fredoka-Regular")
        assert result is not None
        assert "strokes" in result


class TestGetAllCharacters:
    """Tests for get_all_characters function."""

    def test_returns_dict(self):
        """Should return a dictionary."""
        result = get_all_characters()
        assert isinstance(result, dict)

    def test_contains_uppercase(self):
        """Should contain uppercase letters."""
        result = get_all_characters()
        assert "A" in result
        assert "Z" in result

    def test_contains_lowercase(self):
        """Should contain lowercase letters."""
        result = get_all_characters()
        assert "a" in result
        assert "z" in result

    def test_contains_numbers(self):
        """Should contain numbers."""
        result = get_all_characters()
        assert "0" in result
        assert "9" in result

    def test_has_62_characters(self):
        """Should have 62 characters (26 upper + 26 lower + 10 numbers)."""
        result = get_all_characters()
        assert len(result) == 62


class TestGetAvailableFonts:
    """Tests for get_available_fonts function."""

    def test_returns_list(self):
        """Should return a list."""
        result = get_available_fonts()
        assert isinstance(result, list)

    def test_contains_expected_fonts(self):
        """Should contain expected font metadata."""
        result = get_available_fonts()
        font_keys = [f["key"] for f in result]
        assert "fredoka" in font_keys

    def test_each_font_has_required_fields(self):
        """Each font should have required metadata fields."""
        result = get_available_fonts()
        for font in result:
            assert "key" in font
            assert "file_name" in font
            assert "display_name" in font
            assert "style" in font
            assert "description" in font


class TestGetFontMetadata:
    """Tests for get_font_metadata function."""

    def test_returns_metadata_for_default_font(self):
        """Should return metadata for default font."""
        result = get_font_metadata()
        assert result is not None
        assert "display_name" in result

    def test_returns_metadata_for_specific_font(self):
        """Should return metadata for specific font."""
        result = get_font_metadata("Fredoka-Regular")
        assert result is not None
        assert result["display_name"] == "Fredoka"


class TestValidateStrokeFormat:
    """Tests for validate_stroke_format function."""

    def test_valid_stroke(self):
        """Should return True for valid stroke."""
        stroke = {"points": [[0, 0], [100, 100]], "direction": "down"}
        assert validate_stroke_format(stroke) is True

    def test_invalid_missing_points(self):
        """Should return False when points missing."""
        stroke = {"direction": "down"}
        assert validate_stroke_format(stroke) is False

    def test_invalid_missing_direction(self):
        """Should return False when direction missing."""
        stroke = {"points": [[0, 0], [100, 100]]}
        assert validate_stroke_format(stroke) is False

    def test_invalid_not_dict(self):
        """Should return False for non-dict input."""
        assert validate_stroke_format("not a dict") is False

    def test_invalid_single_point(self):
        """Should return False for single point."""
        stroke = {"points": [[0, 0]], "direction": "down"}
        assert validate_stroke_format(stroke) is False

    def test_invalid_point_format(self):
        """Should return False for invalid point format."""
        stroke = {"points": [[0], [100, 100]], "direction": "down"}
        assert validate_stroke_format(stroke) is False


class TestValidateCharacterFormat:
    """Tests for validate_character_format function."""

    def test_valid_character(self):
        """Should return True for valid character data."""
        char_data = {
            "type": "uppercase",
            "phonetic": "ay",
            "sound": "ah",
            "strokes": [{"points": [[0, 0], [100, 100]], "direction": "down"}],
        }
        assert validate_character_format(char_data) is True

    def test_invalid_missing_type(self):
        """Should return False when type missing."""
        char_data = {
            "phonetic": "ay",
            "sound": "ah",
            "strokes": [{"points": [[0, 0], [100, 100]], "direction": "down"}],
        }
        assert validate_character_format(char_data) is False

    def test_invalid_type_value(self):
        """Should return False for invalid type value."""
        char_data = {
            "type": "invalid",
            "phonetic": "ay",
            "sound": "ah",
            "strokes": [{"points": [[0, 0], [100, 100]], "direction": "down"}],
        }
        assert validate_character_format(char_data) is False

    def test_invalid_empty_strokes(self):
        """Should return False for empty strokes."""
        char_data = {
            "type": "uppercase",
            "phonetic": "ay",
            "sound": "ah",
            "strokes": [],
        }
        assert validate_character_format(char_data) is False


class TestClearCache:
    """Tests for clear_cache function."""

    def test_clear_cache_runs(self):
        """Should clear cache without error."""
        # Load some data first
        get_character_strokes("A")
        # Clear cache
        clear_cache()
        # Should still work after clearing
        result = get_character_strokes("A")
        assert result is not None
