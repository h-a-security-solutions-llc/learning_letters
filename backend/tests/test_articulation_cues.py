"""
Unit tests for articulation cues service.

Tests the helper functions and data structures for articulation cues.
"""

import pytest

from app.services.articulation_cues import (
    LETTER_TO_SOUND,
    SOUND_CUES,
    get_all_articulation_data,
    get_articulation_cue,
    get_articulation_media,
    get_hand_cue,
    get_mouth_description,
)


class TestGetArticulationCue:
    """Tests for get_articulation_cue function."""

    def test_returns_cue_for_uppercase_letter(self):
        """Should return cue data for uppercase letters."""
        cue = get_articulation_cue("A")
        assert cue is not None
        assert "mouth_position" in cue
        assert "sound_key" in cue

    def test_returns_cue_for_lowercase_letter(self):
        """Should return cue data for lowercase letters."""
        cue = get_articulation_cue("a")
        assert cue is not None
        assert "mouth_position" in cue

    def test_returns_cue_for_number(self):
        """Should return cue data for numbers."""
        cue = get_articulation_cue("5")
        assert cue is not None
        assert cue["sound_type"] == "number"

    def test_returns_none_for_invalid_character(self):
        """Should return None for unsupported characters."""
        assert get_articulation_cue("@") is None
        assert get_articulation_cue("!") is None
        assert get_articulation_cue("") is None

    def test_returns_copy_not_reference(self):
        """Should return a copy to prevent mutation."""
        cue1 = get_articulation_cue("A")
        cue2 = get_articulation_cue("A")
        # They should be equal but not the same object
        assert cue1 == cue2
        # Modifying one shouldn't affect the other
        cue1["test_field"] = "test"
        assert "test_field" not in cue2

    def test_includes_sound_key(self):
        """Should include the sound_key in the returned data."""
        cue = get_articulation_cue("B")
        assert "sound_key" in cue
        assert cue["sound_key"] == "b"


class TestGetMouthDescription:
    """Tests for get_mouth_description function."""

    def test_returns_description_for_valid_char(self):
        """Should return mouth position description."""
        desc = get_mouth_description("A")
        assert desc is not None
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_returns_none_for_invalid_char(self):
        """Should return None for invalid characters."""
        assert get_mouth_description("@") is None
        assert get_mouth_description("") is None

    def test_descriptions_vary_by_character(self):
        """Different sounds should have different descriptions."""
        desc_a = get_mouth_description("A")
        desc_s = get_mouth_description("S")
        assert desc_a != desc_s


class TestGetHandCue:
    """Tests for get_hand_cue function."""

    def test_returns_cue_for_valid_char(self):
        """Should return hand cue description."""
        cue = get_hand_cue("P")
        assert cue is not None
        assert isinstance(cue, str)
        assert len(cue) > 0

    def test_returns_none_for_invalid_char(self):
        """Should return None for invalid characters."""
        assert get_hand_cue("@") is None

    def test_number_hand_cues_reference_fingers(self):
        """Number hand cues should typically reference finger counting."""
        cue = get_hand_cue("5")
        assert cue is not None
        # Most number cues mention fingers or hands
        assert "finger" in cue.lower() or "hand" in cue.lower()


class TestGetArticulationMedia:
    """Tests for get_articulation_media function."""

    def test_returns_dict_for_valid_char(self):
        """Should return media dict for valid characters."""
        media = get_articulation_media("A")
        assert isinstance(media, dict)

    def test_returns_none_or_empty_for_invalid_char(self):
        """Should return None or empty dict for invalid characters."""
        media = get_articulation_media("@")
        # Function may return None or empty dict for invalid chars
        assert media is None or isinstance(media, dict)


class TestGetAllArticulationData:
    """Tests for get_all_articulation_data function."""

    def test_returns_complete_data(self):
        """Should return all sounds and mappings."""
        data = get_all_articulation_data()

        assert "sounds" in data
        assert "letter_mapping" in data

    def test_sounds_contain_expected_keys(self):
        """Sound data should contain expected phonemes."""
        data = get_all_articulation_data()

        # Check some expected sounds exist
        assert "short_a" in data["sounds"]
        assert "p" in data["sounds"]
        assert "zero" in data["sounds"]

    def test_letter_mapping_covers_all_chars(self):
        """Letter mapping should cover all 62 characters."""
        data = get_all_articulation_data()

        # Should have uppercase, lowercase, and numbers
        mapping = data["letter_mapping"]
        assert len(mapping) >= 62

        # Check specific entries
        assert "A" in mapping
        assert "a" in mapping
        assert "0" in mapping
        assert "9" in mapping


class TestSoundCuesData:
    """Tests for SOUND_CUES data structure."""

    def test_all_sounds_have_required_fields(self):
        """Every sound cue should have required fields."""
        required = ["phoneme", "sound_type", "voiced", "lips_label", "mouth_position", "hand_cue", "teaching_tip"]

        for sound_key, cue in SOUND_CUES.items():
            for field in required:
                assert field in cue, f"Sound '{sound_key}' missing required field '{field}'"

    def test_vowels_are_voiced(self):
        """All vowels should be marked as voiced."""
        vowel_sounds = ["short_a", "short_e", "short_i", "short_o", "short_u"]

        for sound in vowel_sounds:
            if sound in SOUND_CUES:
                assert SOUND_CUES[sound]["voiced"] is True, f"Vowel '{sound}' should be voiced"

    def test_voiceless_consonants_marked_correctly(self):
        """Voiceless consonants should be marked as not voiced."""
        voiceless = ["p", "t", "k", "f", "s", "sh", "ch", "th_voiceless", "h"]

        for sound in voiceless:
            if sound in SOUND_CUES:
                assert SOUND_CUES[sound]["voiced"] is False, f"'{sound}' should be voiceless"

    def test_voiced_consonants_marked_correctly(self):
        """Voiced consonants should be marked as voiced."""
        voiced = ["b", "d", "g", "v", "z", "m", "n", "l", "r", "w", "y"]

        for sound in voiced:
            if sound in SOUND_CUES:
                assert SOUND_CUES[sound]["voiced"] is True, f"'{sound}' should be voiced"

    def test_number_words_have_correct_type(self):
        """All number word cues should have sound_type='number'."""
        number_words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

        for word in number_words:
            assert word in SOUND_CUES, f"Missing number word cue: {word}"
            assert SOUND_CUES[word]["sound_type"] == "number", f"'{word}' should have type 'number'"


class TestLetterToSoundMapping:
    """Tests for LETTER_TO_SOUND mapping."""

    def test_uppercase_letters_mapped(self):
        """All uppercase letters should be mapped."""
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            assert letter in LETTER_TO_SOUND, f"Missing mapping for uppercase '{letter}'"

    def test_lowercase_letters_mapped(self):
        """All lowercase letters should be mapped."""
        for letter in "abcdefghijklmnopqrstuvwxyz":
            assert letter in LETTER_TO_SOUND, f"Missing mapping for lowercase '{letter}'"

    def test_numbers_mapped(self):
        """All numbers 0-9 should be mapped."""
        for num in "0123456789":
            assert num in LETTER_TO_SOUND, f"Missing mapping for number '{num}'"

    def test_mappings_point_to_valid_sounds(self):
        """All mappings should point to sounds that exist in SOUND_CUES."""
        for char, sound_key in LETTER_TO_SOUND.items():
            assert sound_key in SOUND_CUES, f"Character '{char}' maps to non-existent sound '{sound_key}'"

    def test_case_pairs_map_to_same_sound(self):
        """Uppercase and lowercase of same letter should map to same sound."""
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            lower = letter.lower()
            assert LETTER_TO_SOUND[letter] == LETTER_TO_SOUND[lower], f"'{letter}' and '{lower}' should map to same sound"


class TestLiPSLabels:
    """Tests for LiPS (Lindamood-Bell) style labels."""

    def test_stop_consonants_have_labels(self):
        """Stop consonants should have appropriate LiPS labels."""
        # Lip Poppers: p, b
        for sound in ["p", "b"]:
            if sound in SOUND_CUES:
                assert "popper" in SOUND_CUES[sound]["lips_label"].lower() or "lip" in SOUND_CUES[sound][
                    "lips_label"
                ].lower()

        # Tip Tappers: t, d
        for sound in ["t", "d"]:
            if sound in SOUND_CUES:
                label = SOUND_CUES[sound]["lips_label"].lower()
                assert "tapper" in label or "tip" in label

    def test_number_words_have_number_label(self):
        """Number words should have 'Number Word' label."""
        number_words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

        for word in number_words:
            assert SOUND_CUES[word]["lips_label"] == "Number Word"


class TestTeachingContent:
    """Tests for teaching tip quality."""

    def test_teaching_tips_are_substantial(self):
        """Teaching tips should be substantial (not just a word or two)."""
        for sound_key, cue in SOUND_CUES.items():
            tip = cue["teaching_tip"]
            # Should be at least 10 characters
            assert len(tip) >= 10, f"Teaching tip too short for '{sound_key}': {tip}"

    def test_mouth_positions_are_substantial(self):
        """Mouth position descriptions should be descriptive."""
        for sound_key, cue in SOUND_CUES.items():
            desc = cue["mouth_position"]
            # Should be at least 15 characters
            assert len(desc) >= 15, f"Mouth position too short for '{sound_key}': {desc}"

    def test_hand_cues_exist(self):
        """All sounds should have hand cue descriptions."""
        for sound_key, cue in SOUND_CUES.items():
            assert len(cue["hand_cue"]) > 0, f"Empty hand cue for '{sound_key}'"
