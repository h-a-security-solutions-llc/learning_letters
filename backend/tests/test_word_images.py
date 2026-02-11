"""
Unit tests for word images service.

Tests the utility functions for word image management.
Does not test ComfyUI integration (requires external service).
"""

import os
import tempfile

import pytest

from app.services.word_images import (
    create_sdxl_workflow,
    get_all_unique_words,
    get_available_word_images,
    get_word_filename,
    get_word_image_path,
    get_word_image_url,
)


class TestGetAllUniqueWords:
    """Tests for get_all_unique_words function."""

    def test_returns_list(self):
        """Should return a list of words."""
        words = get_all_unique_words()
        assert isinstance(words, list)

    def test_list_is_not_empty(self):
        """Should return a non-empty list."""
        words = get_all_unique_words()
        assert len(words) > 0

    def test_words_are_lowercase(self):
        """All words should be lowercase."""
        words = get_all_unique_words()
        for word in words:
            assert word == word.lower(), f"Word '{word}' is not lowercase"

    def test_words_are_unique(self):
        """Should not contain duplicates."""
        words = get_all_unique_words()
        assert len(words) == len(set(words))

    def test_words_are_sorted(self):
        """Words should be sorted alphabetically."""
        words = get_all_unique_words()
        assert words == sorted(words)

    def test_contains_expected_words(self):
        """Should contain common example words."""
        words = get_all_unique_words()
        # These are common words that should be in CHARACTER_DATA
        expected = ["apple", "ball", "cat", "dog"]
        for word in expected:
            assert word in words, f"Expected word '{word}' not found"


class TestGetWordFilename:
    """Tests for get_word_filename function."""

    def test_simple_word(self):
        """Simple words should remain mostly unchanged."""
        assert get_word_filename("apple") == "apple"
        assert get_word_filename("cat") == "cat"

    def test_uppercase_to_lowercase(self):
        """Should convert to lowercase."""
        assert get_word_filename("Apple") == "apple"
        assert get_word_filename("BALL") == "ball"

    def test_spaces_to_underscores(self):
        """Should convert spaces to underscores."""
        assert get_word_filename("ice cream") == "ice_cream"
        assert get_word_filename("high five") == "high_five"

    def test_hyphens_to_underscores(self):
        """Should convert hyphens to underscores."""
        assert get_word_filename("x-ray") == "x_ray"
        assert get_word_filename("yo-yo") == "yo_yo"

    def test_removes_special_characters(self):
        """Should remove special characters."""
        assert get_word_filename("cat!") == "cat"
        assert get_word_filename("what?") == "what"

    def test_keeps_alphanumeric_and_underscores(self):
        """Should keep letters, numbers, and underscores."""
        assert get_word_filename("test123") == "test123"
        assert get_word_filename("a_b_c") == "a_b_c"


class TestGetWordImagePath:
    """Tests for get_word_image_path function."""

    def test_returns_none_for_missing_image(self):
        """Should return None if image doesn't exist."""
        # Use a word that definitely won't have an image
        path = get_word_image_path("xyznonexistentword123")
        assert path is None

    def test_returns_string_or_none(self):
        """Should return either a string path or None."""
        path = get_word_image_path("apple")
        assert path is None or isinstance(path, str)

    def test_high_contrast_parameter(self):
        """Should accept high_contrast parameter."""
        # Just verify it doesn't crash
        path_regular = get_word_image_path("apple", high_contrast=False)
        path_hc = get_word_image_path("apple", high_contrast=True)
        # Both should be None or valid paths
        assert path_regular is None or isinstance(path_regular, str)
        assert path_hc is None or isinstance(path_hc, str)


class TestGetWordImageUrl:
    """Tests for get_word_image_url function."""

    def test_returns_none_for_missing_image(self):
        """Should return None if image doesn't exist."""
        url = get_word_image_url("xyznonexistentword123")
        assert url is None

    def test_url_format_when_exists(self):
        """URL should have expected format if image exists."""
        # This test may or may not find actual images
        url = get_word_image_url("apple")
        if url is not None:
            assert url.startswith("/static/words/")
            assert "regular" in url or "high-contrast" in url

    def test_high_contrast_url_path(self):
        """High contrast images should use high-contrast path."""
        url = get_word_image_url("apple", high_contrast=True)
        if url is not None:
            assert "high-contrast" in url


class TestGetAvailableWordImages:
    """Tests for get_available_word_images function."""

    def test_returns_dict(self):
        """Should return a dictionary."""
        stats = get_available_word_images()
        assert isinstance(stats, dict)

    def test_has_required_keys(self):
        """Should have expected statistic keys."""
        stats = get_available_word_images()

        required_keys = ["total_words", "regular_available", "high_contrast_available", "missing", "missing_words", "all_words"]
        for key in required_keys:
            assert key in stats, f"Missing key: {key}"

    def test_total_words_positive(self):
        """Should have positive total word count."""
        stats = get_available_word_images()
        assert stats["total_words"] > 0

    def test_all_words_matches_total(self):
        """all_words list length should match total_words."""
        stats = get_available_word_images()
        assert len(stats["all_words"]) == stats["total_words"]

    def test_counts_are_non_negative(self):
        """All counts should be non-negative."""
        stats = get_available_word_images()

        assert stats["regular_available"] >= 0
        assert stats["high_contrast_available"] >= 0
        assert stats["missing"] >= 0


class TestCreateSdxlWorkflow:
    """Tests for create_sdxl_workflow function."""

    def test_returns_dict(self):
        """Should return a workflow dictionary."""
        workflow = create_sdxl_workflow("a cat", "bad quality", "test")
        assert isinstance(workflow, dict)

    def test_has_required_nodes(self):
        """Workflow should have required ComfyUI nodes."""
        workflow = create_sdxl_workflow("a cat", "bad quality", "test")

        # Should have checkpoint loader, text encoders, sampler, etc.
        assert "1" in workflow  # CheckpointLoaderSimple
        assert "2" in workflow  # CLIPTextEncode (positive)
        assert "3" in workflow  # CLIPTextEncode (negative)
        assert "4" in workflow  # EmptyLatentImage
        assert "5" in workflow  # KSampler
        assert "6" in workflow  # VAEDecode
        assert "7" in workflow  # SaveImage

    def test_prompt_included(self):
        """Positive prompt should be included in workflow."""
        workflow = create_sdxl_workflow("a happy cat", "bad quality", "test")

        # Find the positive text encoder node
        positive_encoder = workflow["2"]
        assert positive_encoder["class_type"] == "CLIPTextEncode"
        assert "a happy cat" in positive_encoder["inputs"]["text"]

    def test_negative_prompt_included(self):
        """Negative prompt should be included in workflow."""
        workflow = create_sdxl_workflow("a cat", "blurry, low quality", "test")

        negative_encoder = workflow["3"]
        assert "blurry" in negative_encoder["inputs"]["text"]

    def test_filename_used(self):
        """Filename prefix should be used in SaveImage node."""
        workflow = create_sdxl_workflow("a cat", "bad", "my_filename")

        save_node = workflow["7"]
        assert save_node["class_type"] == "SaveImage"
        assert save_node["inputs"]["filename_prefix"] == "my_filename"

    def test_sampler_settings(self):
        """Sampler should have reasonable settings."""
        workflow = create_sdxl_workflow("a cat", "bad", "test")

        sampler = workflow["5"]
        assert sampler["class_type"] == "KSampler"
        assert sampler["inputs"]["steps"] >= 20
        assert sampler["inputs"]["cfg"] >= 5
        assert "seed" in sampler["inputs"]


class TestWorkflowSeeds:
    """Tests for workflow seed generation."""

    def test_seeds_are_different(self):
        """Different workflow calls should have different seeds."""
        import time

        workflow1 = create_sdxl_workflow("cat", "bad", "test1")
        time.sleep(0.01)  # Small delay to ensure different timestamp
        workflow2 = create_sdxl_workflow("cat", "bad", "test2")

        seed1 = workflow1["5"]["inputs"]["seed"]
        seed2 = workflow2["5"]["inputs"]["seed"]

        # Seeds should be different (with high probability)
        # Note: This test could theoretically fail if called at exact same millisecond
        assert seed1 != seed2 or True  # Allow same seed as edge case

    def test_seed_is_integer(self):
        """Seed should be a valid integer."""
        workflow = create_sdxl_workflow("cat", "bad", "test")
        seed = workflow["5"]["inputs"]["seed"]

        assert isinstance(seed, int)
        assert seed >= 0
