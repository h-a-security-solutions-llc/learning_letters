"""Tests for trace_generator service."""

import numpy as np

from app.services.trace_generator import (
    count_neighbors,
    deduplicate_paths,
    find_special_points,
    generate_all_guides,
    generate_animated_guide_data,
    generate_character_image,
    generate_font_preview,
    generate_trace_image,
    get_available_fonts,
    get_font,
    simplify_path,
)


class TestGetFont:
    """Tests for get_font function."""

    def test_returns_font(self):
        """Should return a font object."""
        font = get_font(48)
        assert font is not None

    def test_different_sizes(self):
        """Should work with different sizes."""
        for size in [24, 48, 72, 100]:
            font = get_font(size)
            assert font is not None

    def test_with_font_name(self):
        """Should accept font_name parameter."""
        font = get_font(48, font_name="Fredoka-Regular")
        assert font is not None


class TestGetAvailableFonts:
    """Tests for get_available_fonts function."""

    def test_returns_list(self):
        """Should return a list."""
        result = get_available_fonts()
        assert isinstance(result, list)

    def test_contains_fredoka(self):
        """Should contain Fredoka font."""
        result = get_available_fonts()
        assert any("Fredoka" in f for f in result)


class TestGenerateCharacterImage:
    """Tests for generate_character_image function."""

    def test_returns_array(self):
        """Should return numpy array."""
        result = generate_character_image("A")
        assert isinstance(result, np.ndarray)

    def test_correct_size(self):
        """Should return image of specified size."""
        result = generate_character_image("A", size=400)
        assert result.shape == (400, 400)

    def test_has_content(self):
        """Should have drawn content (not all white)."""
        result = generate_character_image("A")
        # Should have some dark pixels (character)
        assert np.min(result) < 200

    def test_different_characters(self):
        """Should work for different characters."""
        for char in ["A", "a", "1", "Z", "z", "9"]:
            result = generate_character_image(char)
            assert result is not None


class TestCountNeighbors:
    """Tests for count_neighbors function."""

    def test_isolated_pixel(self):
        """Should return 0 for isolated pixel."""
        skeleton = np.zeros((10, 10), dtype=bool)
        skeleton[5, 5] = True
        count = count_neighbors(skeleton, 5, 5)
        assert count == 0

    def test_line_endpoint(self):
        """Should return 1 for line endpoint."""
        skeleton = np.zeros((10, 10), dtype=bool)
        skeleton[5, 5] = True
        skeleton[5, 6] = True
        count = count_neighbors(skeleton, 5, 5)
        assert count == 1

    def test_line_middle(self):
        """Should return 2 for middle of line."""
        skeleton = np.zeros((10, 10), dtype=bool)
        skeleton[5, 4:7] = True  # Horizontal line of 3
        count = count_neighbors(skeleton, 5, 5)
        assert count == 2

    def test_junction(self):
        """Should return 3+ for junction point."""
        skeleton = np.zeros((10, 10), dtype=bool)
        skeleton[5, 4:7] = True  # Horizontal line
        skeleton[4, 5] = True  # Vertical branch
        count = count_neighbors(skeleton, 5, 5)
        assert count == 3


class TestFindSpecialPoints:
    """Tests for find_special_points function."""

    def test_finds_endpoints(self):
        """Should find endpoints of a line."""
        skeleton = np.zeros((10, 10), dtype=bool)
        skeleton[5, 2:8] = True  # Horizontal line
        endpoints, junctions = find_special_points(skeleton)
        assert len(endpoints) == 2
        assert len(junctions) == 0

    def test_finds_junction(self):
        """Should find junction point."""
        skeleton = np.zeros((10, 10), dtype=bool)
        skeleton[5, 2:8] = True  # Horizontal line
        skeleton[3:7, 5] = True  # Vertical line crossing
        endpoints, junctions = find_special_points(skeleton)
        assert len(junctions) >= 1


class TestDeduplicatePaths:
    """Tests for deduplicate_paths function."""

    def test_empty_list(self):
        """Should handle empty list."""
        result = deduplicate_paths([])
        assert result == []

    def test_no_duplicates(self):
        """Should keep non-overlapping paths."""
        paths = [
            [(0, 0), (10, 10)],
            [(100, 100), (110, 110)],
        ]
        result = deduplicate_paths(paths)
        assert len(result) == 2

    def test_removes_duplicates(self):
        """Should remove duplicate paths."""
        paths = [
            [(0, 0), (5, 5), (10, 10)],
            [(0, 0), (5, 5), (10, 10)],  # Exact duplicate
        ]
        result = deduplicate_paths(paths)
        assert len(result) == 1

    def test_keeps_longer_path(self):
        """Should keep longer path when overlapping."""
        short_path = [(0, 0), (5, 5)]
        long_path = [(0, 0), (5, 5), (10, 10), (15, 15)]
        paths = [short_path, long_path]
        result = deduplicate_paths(paths)
        assert len(result) == 1
        assert len(result[0]) == 4  # Kept the longer one


class TestSimplifyPath:
    """Tests for simplify_path function."""

    def test_short_path(self):
        """Should return short path unchanged."""
        path = [(0, 0)]
        result = simplify_path(path)
        assert result == path

    def test_simplifies_close_points(self):
        """Should remove points too close together."""
        path = [(0, 0), (1, 1), (2, 2), (10, 10)]
        result = simplify_path(path, tolerance=5)
        # Should keep start, skip middle close points, keep end
        assert len(result) < len(path)
        assert result[0] == (0, 0)
        assert result[-1] == (10, 10)

    def test_keeps_distant_points(self):
        """Should keep points far apart."""
        path = [(0, 0), (50, 50), (100, 100)]
        result = simplify_path(path, tolerance=3)
        assert len(result) == 3


class TestGenerateAnimatedGuideData:
    """Tests for generate_animated_guide_data function."""

    def test_returns_dict(self):
        """Should return a dictionary."""
        result = generate_animated_guide_data("A")
        assert isinstance(result, dict)

    def test_has_required_fields(self):
        """Should have required fields."""
        result = generate_animated_guide_data("A")
        assert "character" in result
        assert "size" in result
        assert "strokes" in result
        assert "stroke_count" in result

    def test_strokes_have_required_fields(self):
        """Each stroke should have required fields."""
        result = generate_animated_guide_data("A")
        for stroke in result["strokes"]:
            assert "points" in stroke
            assert "color" in stroke
            assert "order" in stroke

    def test_normalized_coordinates(self):
        """Stroke points should be in 0-100 range."""
        result = generate_animated_guide_data("A")
        for stroke in result["strokes"]:
            for point in stroke["points"]:
                assert 0 <= point[0] <= 100
                assert 0 <= point[1] <= 100


class TestGenerateTraceImage:
    """Tests for generate_trace_image function."""

    def test_returns_base64(self):
        """Should return base64 data URL."""
        result = generate_trace_image("A")
        assert result.startswith("data:image/png;base64,")

    def test_different_characters(self):
        """Should work for different characters."""
        for char in ["A", "a", "1"]:
            result = generate_trace_image(char)
            assert result.startswith("data:image/png;base64,")

    def test_different_sizes(self):
        """Should work with different sizes."""
        for size in [200, 400, 600]:
            result = generate_trace_image("A", size=size)
            assert result.startswith("data:image/png;base64,")


class TestGenerateAllGuides:
    """Tests for generate_all_guides function."""

    def test_returns_dict(self):
        """Should return a dictionary."""
        result = generate_all_guides("A")
        assert isinstance(result, dict)

    def test_has_required_fields(self):
        """Should have required fields."""
        result = generate_all_guides("A")
        assert "character" in result
        assert "size" in result
        assert "trace_image" in result
        assert "animated_strokes" in result
        assert "stroke_count" in result
        assert "font_name" in result

    def test_trace_image_is_base64(self):
        """Trace image should be base64 data URL."""
        result = generate_all_guides("A")
        assert result["trace_image"].startswith("data:image/png;base64,")


class TestGenerateFontPreview:
    """Tests for generate_font_preview function."""

    def test_returns_base64(self):
        """Should return base64 data URL."""
        result = generate_font_preview("Fredoka-Regular")
        assert result.startswith("data:image/png;base64,")

    def test_different_fonts(self):
        """Should work for different fonts."""
        fonts = get_available_fonts()
        for font in fonts[:2]:  # Test first 2 to save time
            result = generate_font_preview(font)
            assert result.startswith("data:image/png;base64,")
