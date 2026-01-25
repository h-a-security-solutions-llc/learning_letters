"""Tests for audio_generator service."""

from app.services.audio_generator import (
    CHARACTER_DATA,
    DEFAULT_VOICES,
    ELEVENLABS_VOICES,
    build_speech_text,
    get_audio_path,
    get_available_voices,
    get_available_words,
    get_character_data,
    get_random_word,
)


class TestCharacterData:
    """Tests for CHARACTER_DATA constants."""

    def test_has_uppercase(self):
        """Should have all uppercase letters."""
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            assert char in CHARACTER_DATA

    def test_has_lowercase(self):
        """Should have all lowercase letters."""
        for char in "abcdefghijklmnopqrstuvwxyz":
            assert char in CHARACTER_DATA

    def test_has_numbers(self):
        """Should have all numbers 0-9."""
        for char in "0123456789":
            assert char in CHARACTER_DATA

    def test_has_62_characters(self):
        """Should have exactly 62 characters."""
        assert len(CHARACTER_DATA) == 62

    def test_each_has_required_fields(self):
        """Each character should have required fields."""
        for _char, data in CHARACTER_DATA.items():
            assert "type" in data
            assert "name" in data
            assert "sound" in data
            assert "words" in data
            assert data["type"] in ["uppercase", "lowercase", "number"]


class TestVoiceData:
    """Tests for voice constants."""

    def test_elevenlabs_voices_has_entries(self):
        """Should have voice entries."""
        assert len(ELEVENLABS_VOICES) >= 2

    def test_each_voice_has_required_fields(self):
        """Each voice should have required fields."""
        for _voice_name, voice_data in ELEVENLABS_VOICES.items():
            assert "id" in voice_data
            assert "gender" in voice_data
            assert "name" in voice_data
            assert "description" in voice_data

    def test_default_voices_mapped(self):
        """Default voices should map to valid voices."""
        for _gender, voice in DEFAULT_VOICES.items():
            assert voice in ELEVENLABS_VOICES


class TestGetCharacterData:
    """Tests for get_character_data function."""

    def test_returns_data_for_uppercase(self):
        """Should return data for uppercase letter."""
        result = get_character_data("A")
        assert result is not None
        assert result["type"] == "uppercase"

    def test_returns_data_for_lowercase(self):
        """Should return data for lowercase letter."""
        result = get_character_data("a")
        assert result is not None
        assert result["type"] == "lowercase"

    def test_returns_data_for_number(self):
        """Should return data for number."""
        result = get_character_data("5")
        assert result is not None
        assert result["type"] == "number"

    def test_returns_none_for_unknown(self):
        """Should return None for unknown character."""
        result = get_character_data("@")
        assert result is None


class TestGetRandomWord:
    """Tests for get_random_word function."""

    def test_returns_word_for_letter(self):
        """Should return a word for letter."""
        result = get_random_word("A")
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_word_from_list(self):
        """Should return word from character's word list."""
        result = get_random_word("A")
        assert result in CHARACTER_DATA["A"]["words"]

    def test_returns_empty_for_unknown(self):
        """Should return empty string for unknown character."""
        result = get_random_word("@")
        assert result == ""


class TestBuildSpeechText:
    """Tests for build_speech_text function."""

    def test_builds_text_for_uppercase(self):
        """Should build speech text for uppercase letter."""
        result = build_speech_text("A")
        assert "Capital A" in result
        assert "ah" in result

    def test_builds_text_for_lowercase(self):
        """Should build speech text for lowercase letter."""
        result = build_speech_text("a")
        assert "Lowercase a" in result
        assert "ah" in result

    def test_builds_text_for_number(self):
        """Should build speech text for number."""
        result = build_speech_text("5")
        assert "Five" in result
        assert "five" in result

    def test_includes_word(self):
        """Should include example word."""
        result = build_speech_text("A", word="apple")
        assert "apple" in result

    def test_uses_random_word_if_not_provided(self):
        """Should use random word if not provided."""
        result = build_speech_text("A")
        # Should contain "as in [word]"
        assert "as in" in result

    def test_returns_character_for_unknown(self):
        """Should return just character for unknown."""
        result = build_speech_text("@")
        assert result == "@"


class TestGetAudioPath:
    """Tests for get_audio_path function."""

    def test_uppercase_path(self):
        """Should create correct path for uppercase."""
        result = get_audio_path("A", "rachel")
        assert "upper_A" in result
        assert "rachel" in result
        assert result.endswith(".mp3")

    def test_lowercase_path(self):
        """Should create correct path for lowercase."""
        result = get_audio_path("a", "rachel")
        assert "lower_a" in result
        assert "rachel" in result

    def test_number_path(self):
        """Should create correct path for number."""
        result = get_audio_path("5", "rachel")
        assert "num_5" in result

    def test_different_voices(self):
        """Should use voice in path."""
        for voice in ["rachel", "adam"]:
            result = get_audio_path("A", voice)
            assert voice in result


class TestGetAvailableVoices:
    """Tests for get_available_voices function."""

    def test_returns_dict(self):
        """Should return a dictionary."""
        result = get_available_voices()
        assert isinstance(result, dict)

    def test_has_voices_key(self):
        """Should have voices key."""
        result = get_available_voices()
        assert "voices" in result

    def test_voices_have_required_fields(self):
        """Each voice should have required fields."""
        result = get_available_voices()
        for voice in result["voices"]:
            assert "id" in voice
            assert "name" in voice
            assert "gender" in voice
            assert "description" in voice


class TestGetAvailableWords:
    """Tests for get_available_words function."""

    def test_returns_list_for_letter(self):
        """Should return list of words for letter."""
        result = get_available_words("A")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_returns_expected_words(self):
        """Should return words from character data."""
        result = get_available_words("A")
        assert "apple" in result

    def test_returns_empty_for_unknown(self):
        """Should return empty list for unknown character."""
        result = get_available_words("@")
        assert result == []
