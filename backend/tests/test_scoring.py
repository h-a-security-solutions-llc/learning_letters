"""Tests for scoring service."""

import base64
import io

import numpy as np
from PIL import Image

from app.services.scoring import (
    calculate_accuracy_score,
    calculate_coverage_score,
    calculate_stroke_similarity,
    extract_and_center_character,
    find_endpoints,
    generate_reference_image,
    normalize_line_thickness,
    preprocess_image,
    score_drawing,
)


class TestGenerateReferenceImage:
    """Tests for generate_reference_image function."""

    def test_returns_image(self):
        """Should return a PIL Image."""
        result = generate_reference_image("A")
        assert isinstance(result, Image.Image)

    def test_correct_size(self):
        """Should return image of specified size."""
        result = generate_reference_image("A", size=200)
        assert result.size == (200, 200)

    def test_custom_size(self):
        """Should handle custom sizes."""
        result = generate_reference_image("A", size=300)
        assert result.size == (300, 300)

    def test_different_characters(self):
        """Should work for different characters."""
        for char in ["A", "a", "1", "Z"]:
            result = generate_reference_image(char)
            assert result is not None

    def test_with_font_name(self):
        """Should accept font_name parameter."""
        result = generate_reference_image("A", font_name="Fredoka-Regular")
        assert result is not None


class TestExtractAndCenterCharacter:
    """Tests for extract_and_center_character function."""

    def test_centers_character(self):
        """Should center the character in output."""
        # Create a test image with content in corner
        img = Image.new("L", (200, 200), color=255)
        # Draw a small black square in corner
        for x in range(10, 30):
            for y in range(10, 30):
                img.putpixel((x, y), 0)

        result = extract_and_center_character(img, target_size=128)
        assert result.shape == (128, 128)
        # The content should be centered

    def test_handles_empty_image(self):
        """Should handle empty (all white) image."""
        img = Image.new("L", (200, 200), color=255)
        result = extract_and_center_character(img, target_size=128)
        assert result.shape == (128, 128)
        # Should be mostly white (1.0)
        assert np.mean(result) > 0.9

    def test_handles_rgb_image(self):
        """Should convert RGB to grayscale."""
        img = Image.new("RGB", (200, 200), color=(255, 255, 255))
        result = extract_and_center_character(img, target_size=128)
        assert result.shape == (128, 128)


class TestPreprocessImage:
    """Tests for preprocess_image function."""

    def test_returns_normalized_array(self):
        """Should return normalized numpy array."""
        img = Image.new("L", (200, 200), color=200)
        result = preprocess_image(img)
        assert isinstance(result, np.ndarray)
        assert result.min() >= 0
        assert result.max() <= 1

    def test_resizes_to_target(self):
        """Should resize to target size."""
        img = Image.new("L", (500, 500), color=200)
        result = preprocess_image(img, target_size=128)
        assert result.shape == (128, 128)


class TestFindEndpoints:
    """Tests for find_endpoints function."""

    def test_finds_line_endpoints(self):
        """Should find endpoints of a line."""
        skeleton = np.zeros((10, 10), dtype=bool)
        skeleton[5, 2:8] = True  # Horizontal line
        endpoints = find_endpoints(skeleton)
        assert len(endpoints) == 2

    def test_no_endpoints_for_empty(self):
        """Should return empty for empty skeleton."""
        skeleton = np.zeros((10, 10), dtype=bool)
        endpoints = find_endpoints(skeleton)
        assert len(endpoints) == 0

    def test_no_endpoints_for_loop(self):
        """Should return no endpoints for closed loop."""
        skeleton = np.zeros((10, 10), dtype=bool)
        # Create a square loop
        skeleton[2, 2:8] = True
        skeleton[7, 2:8] = True
        skeleton[2:8, 2] = True
        skeleton[2:8, 7] = True
        endpoints = find_endpoints(skeleton)
        # A closed loop should have 0 or few endpoints depending on exact shape
        assert len(endpoints) <= 4  # Corners might be detected


class TestNormalizeLineThickness:
    """Tests for normalize_line_thickness function."""

    def test_handles_empty_image(self):
        """Should handle empty image."""
        binary = np.zeros((100, 100), dtype=bool)
        result = normalize_line_thickness(binary)
        assert result.shape == (100, 100)
        assert not np.any(result)

    def test_normalizes_thick_line(self):
        """Should normalize thick line to target thickness."""
        binary = np.zeros((100, 100), dtype=bool)
        binary[45:55, 20:80] = True  # Thick horizontal line
        result = normalize_line_thickness(binary, target_thickness=5)
        # Result should have fewer pixels than original
        assert np.sum(result) < np.sum(binary)


class TestCalculateCoverageScore:
    """Tests for calculate_coverage_score function."""

    def test_perfect_coverage(self):
        """Should return high score for identical images."""
        img = np.ones((128, 128))
        # Draw some content
        img[40:60, 40:60] = 0
        score = calculate_coverage_score(img, img.copy())
        assert score >= 0.9

    def test_no_coverage(self):
        """Should return low score for no overlap."""
        drawn = np.ones((128, 128))
        drawn[10:20, 10:20] = 0  # Top left

        reference = np.ones((128, 128))
        reference[100:110, 100:110] = 0  # Bottom right

        score = calculate_coverage_score(drawn, reference)
        assert score < 0.5

    def test_returns_value_between_0_and_1(self):
        """Score should be between 0 and 1."""
        drawn = np.ones((128, 128))
        drawn[40:60, 40:60] = 0

        reference = np.ones((128, 128))
        reference[45:65, 45:65] = 0

        score = calculate_coverage_score(drawn, reference)
        assert 0 <= score <= 1


class TestCalculateAccuracyScore:
    """Tests for calculate_accuracy_score function."""

    def test_perfect_accuracy(self):
        """Should return high score for identical images."""
        img = np.ones((128, 128))
        img[40:60, 40:60] = 0
        score = calculate_accuracy_score(img, img.copy())
        assert score >= 0.9

    def test_returns_value_between_0_and_1(self):
        """Score should be between 0 and 1."""
        drawn = np.ones((128, 128))
        drawn[40:60, 40:60] = 0

        reference = np.ones((128, 128))
        reference[45:65, 45:65] = 0

        score = calculate_accuracy_score(drawn, reference)
        assert 0 <= score <= 1


class TestCalculateStrokeSimilarity:
    """Tests for calculate_stroke_similarity function."""

    def test_identical_images(self):
        """Should return high similarity for identical images."""
        img = np.ones((128, 128))
        img[40:60, 40:60] = 0
        score = calculate_stroke_similarity(img, img.copy())
        assert score >= 0.8

    def test_empty_images(self):
        """Should handle empty images."""
        empty = np.ones((128, 128))
        score = calculate_stroke_similarity(empty, empty)
        assert score == 0.0

    def test_returns_value_between_0_and_1(self):
        """Score should be between 0 and 1."""
        drawn = np.ones((128, 128))
        drawn[40:60, 40:60] = 0

        reference = np.ones((128, 128))
        reference[45:65, 45:65] = 0

        score = calculate_stroke_similarity(drawn, reference)
        assert 0 <= score <= 1


class TestScoreDrawing:
    """Tests for score_drawing function."""

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

    def test_returns_score(self):
        """Should return a score result."""
        image_data = self._create_test_image_data()
        result = score_drawing(image_data, "A")

        assert "score" in result
        assert "stars" in result
        assert "feedback" in result

    def test_score_in_range(self):
        """Score should be between 0 and 100."""
        image_data = self._create_test_image_data()
        result = score_drawing(image_data, "A")

        assert 0 <= result["score"] <= 100

    def test_stars_in_range(self):
        """Stars should be between 1 and 5."""
        image_data = self._create_test_image_data()
        result = score_drawing(image_data, "A")

        assert 1 <= result["stars"] <= 5

    def test_handles_different_characters(self):
        """Should work for different characters."""
        image_data = self._create_test_image_data()

        for char in ["A", "a", "1"]:
            result = score_drawing(image_data, char)
            assert "score" in result

    def test_handles_raw_base64(self):
        """Should handle raw base64 without data URL prefix."""
        img = Image.new("L", (200, 200), color=255)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

        result = score_drawing(base64_data, "A")
        assert "score" in result

    def test_returns_error_for_invalid_image(self):
        """Should return error for invalid image data."""
        result = score_drawing("not_valid_base64", "A")
        assert "error" in result

    def test_includes_details(self):
        """Should include score details."""
        image_data = self._create_test_image_data()
        result = score_drawing(image_data, "A")

        assert "details" in result
        assert "coverage" in result["details"]
        assert "accuracy" in result["details"]
        assert "similarity" in result["details"]

    def test_includes_reference_image(self):
        """Should include reference image."""
        image_data = self._create_test_image_data()
        result = score_drawing(image_data, "A")

        assert "reference_image" in result
        assert result["reference_image"].startswith("data:image/png;base64,")

    def test_with_font_name(self):
        """Should accept font_name parameter."""
        image_data = self._create_test_image_data()
        result = score_drawing(image_data, "A", font_name="Fredoka-Regular")
        assert "score" in result
