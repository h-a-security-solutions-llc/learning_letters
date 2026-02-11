"""
Stroke Alignment Tests

Tests that step-by-step guided strokes align with font skeletons within acceptable
tolerances. If these tests fail, students following the guides would be penalized
during validation.

The tolerance thresholds match those used in stroke validation, ensuring that
if a student traces the guide perfectly, they will pass validation.
"""

import math
import pytest
import numpy as np
from typing import List, Tuple, Optional

from app.services.stroke_path_generator import (
    generate_hybrid_stroke_data,
    get_skeleton_bounds,
)
from app.services.trace_generator import (
    generate_character_image,
    generate_animated_guide_data,
)
from app.services.font_strokes import get_character_strokes, FONT_METADATA
from skimage.morphology import skeletonize


# Test configuration
CANVAS_SIZE = 400

# Tolerance thresholds (as percentage of canvas size)
# These match the validation tolerances used when checking student drawings
BOUNDS_TOLERANCE_PERCENT = 0.06  # 6% - stroke bounds must be within this of skeleton
PATH_TOLERANCE_PERCENT = 0.12   # 12% - path points must be within this of skeleton
START_END_TOLERANCE_PERCENT = 0.10  # 10% - start/end points critical for validation

# Characters to test (all uppercase, lowercase, and digits)
UPPERCASE = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
LOWERCASE = list("abcdefghijklmnopqrstuvwxyz")
DIGITS = list("0123456789")

# Fonts to test
FONTS_TO_TEST = ["Fredoka-Regular", "Nunito-Regular"]


def get_skeleton_pixels(character: str, size: int, font_name: str) -> np.ndarray:
    """Get the skeleton as a binary image."""
    img = generate_character_image(character, size, font_name)
    binary = img < 128
    return skeletonize(binary)


def point_to_skeleton_distance(
    point: Tuple[float, float],
    skeleton: np.ndarray,
    size: int
) -> float:
    """
    Calculate minimum distance from a point to the nearest skeleton pixel.
    Point is in 0-100 normalized space, skeleton is in pixel space.
    """
    # Convert point from 0-100 space to pixel space
    px = int(point[0] * size / 100)
    py = int(point[1] * size / 100)

    # Find all skeleton pixel coordinates
    skeleton_coords = np.argwhere(skeleton)
    if len(skeleton_coords) == 0:
        return float('inf')

    # Calculate distances to all skeleton pixels
    # skeleton_coords are (y, x) pairs
    distances = np.sqrt(
        (skeleton_coords[:, 1] - px) ** 2 +
        (skeleton_coords[:, 0] - py) ** 2
    )

    # Return minimum distance in normalized 0-100 space
    return float(np.min(distances)) * 100 / size


def calculate_path_skeleton_deviation(
    points: List[List[float]],
    skeleton: np.ndarray,
    size: int
) -> dict:
    """
    Calculate how well a path aligns with the skeleton.

    Returns:
        dict with avg_distance, max_distance, percent_within_tolerance
    """
    if not points:
        return {"avg_distance": float('inf'), "max_distance": float('inf'), "percent_within_tolerance": 0}

    distances = []
    tolerance = size * PATH_TOLERANCE_PERCENT
    within_tolerance = 0

    for point in points:
        dist = point_to_skeleton_distance((point[0], point[1]), skeleton, size)
        distances.append(dist)
        if dist <= PATH_TOLERANCE_PERCENT * 100:  # Compare in 0-100 space
            within_tolerance += 1

    return {
        "avg_distance": sum(distances) / len(distances),
        "max_distance": max(distances),
        "percent_within_tolerance": within_tolerance / len(distances) * 100
    }


def calculate_bounds_deviation(
    skeleton_bounds: Tuple[float, float, float, float],
    stroke_bounds: Tuple[float, float, float, float]
) -> dict:
    """
    Calculate deviation between skeleton bounds and stroke bounds.
    All values in 0-100 normalized space.
    """
    s_min_x, s_min_y, s_max_x, s_max_y = skeleton_bounds
    t_min_x, t_min_y, t_max_x, t_max_y = stroke_bounds

    return {
        "x_start_diff": abs(s_min_x - t_min_x),
        "x_end_diff": abs(s_max_x - t_max_x),
        "y_start_diff": abs(s_min_y - t_min_y),
        "y_end_diff": abs(s_max_y - t_max_y),
        "max_diff": max(
            abs(s_min_x - t_min_x),
            abs(s_max_x - t_max_x),
            abs(s_min_y - t_min_y),
            abs(s_max_y - t_max_y)
        )
    }


class TestStrokeSkeletonAlignment:
    """Test that guided strokes align with font skeletons."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.bounds_tolerance = BOUNDS_TOLERANCE_PERCENT * 100  # In 0-100 space
        self.path_tolerance = PATH_TOLERANCE_PERCENT * 100
        self.start_end_tolerance = START_END_TOLERANCE_PERCENT * 100

    def get_stroke_bounds(self, strokes: List[dict]) -> Tuple[float, float, float, float]:
        """Get combined bounds of all strokes."""
        all_points = []
        for stroke in strokes:
            all_points.extend(stroke["points"])

        if not all_points:
            return (0, 0, 100, 100)

        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        return (min(xs), min(ys), max(xs), max(ys))

    @pytest.mark.parametrize("font", FONTS_TO_TEST)
    @pytest.mark.parametrize("character", UPPERCASE)
    def test_uppercase_bounds_alignment(self, font: str, character: str):
        """Test that uppercase letter stroke bounds align with skeleton."""
        self._test_bounds_alignment(character, font)

    @pytest.mark.parametrize("font", FONTS_TO_TEST)
    @pytest.mark.parametrize("character", LOWERCASE)
    def test_lowercase_bounds_alignment(self, font: str, character: str):
        """Test that lowercase letter stroke bounds align with skeleton."""
        self._test_bounds_alignment(character, font)

    @pytest.mark.parametrize("font", FONTS_TO_TEST)
    @pytest.mark.parametrize("character", DIGITS)
    def test_digit_bounds_alignment(self, font: str, character: str):
        """Test that digit stroke bounds align with skeleton."""
        self._test_bounds_alignment(character, font)

    def _test_bounds_alignment(self, character: str, font: str):
        """Test that stroke bounds align with skeleton bounds."""
        # Skip if no stroke data for this character/font
        json_data = get_character_strokes(character, font)
        if json_data is None:
            pytest.skip(f"No stroke data for '{character}' in {font}")

        # Get skeleton bounds
        skeleton_bounds = get_skeleton_bounds(character, CANVAS_SIZE, font)
        if skeleton_bounds is None:
            pytest.skip(f"Could not extract skeleton for '{character}' in {font}")

        # Get guided stroke data
        stroke_data = generate_hybrid_stroke_data(character, CANVAS_SIZE, font)
        if stroke_data is None:
            pytest.fail(f"Failed to generate stroke data for '{character}' in {font}")

        stroke_bounds = self.get_stroke_bounds(stroke_data["strokes"])

        # Calculate deviation
        deviation = calculate_bounds_deviation(skeleton_bounds, stroke_bounds)

        # Assert bounds are within tolerance
        assert deviation["max_diff"] <= self.bounds_tolerance, (
            f"Bounds deviation too large for '{character}' in {font}:\n"
            f"  Skeleton bounds: X {skeleton_bounds[0]:.1f}-{skeleton_bounds[2]:.1f}, "
            f"Y {skeleton_bounds[1]:.1f}-{skeleton_bounds[3]:.1f}\n"
            f"  Stroke bounds:   X {stroke_bounds[0]:.1f}-{stroke_bounds[2]:.1f}, "
            f"Y {stroke_bounds[1]:.1f}-{stroke_bounds[3]:.1f}\n"
            f"  Max deviation: {deviation['max_diff']:.1f} (tolerance: {self.bounds_tolerance:.1f})\n"
            f"  Students following this guide would be penalized!"
        )

    @pytest.mark.parametrize("font", FONTS_TO_TEST)
    @pytest.mark.parametrize("character", UPPERCASE)
    def test_uppercase_path_alignment(self, font: str, character: str):
        """Test that uppercase letter stroke paths align with skeleton."""
        self._test_path_alignment(character, font)

    @pytest.mark.parametrize("font", FONTS_TO_TEST)
    @pytest.mark.parametrize("character", LOWERCASE)
    def test_lowercase_path_alignment(self, font: str, character: str):
        """Test that lowercase letter stroke paths align with skeleton."""
        self._test_path_alignment(character, font)

    @pytest.mark.parametrize("font", FONTS_TO_TEST)
    @pytest.mark.parametrize("character", DIGITS)
    def test_digit_path_alignment(self, font: str, character: str):
        """Test that digit stroke paths align with skeleton."""
        self._test_path_alignment(character, font)

    def _test_path_alignment(self, character: str, font: str):
        """Test that stroke path points are close to skeleton."""
        # Skip if no stroke data
        json_data = get_character_strokes(character, font)
        if json_data is None:
            pytest.skip(f"No stroke data for '{character}' in {font}")

        # Get skeleton
        skeleton = get_skeleton_pixels(character, CANVAS_SIZE, font)
        if not skeleton.any():
            pytest.skip(f"Empty skeleton for '{character}' in {font}")

        # Get guided strokes
        stroke_data = generate_hybrid_stroke_data(character, CANVAS_SIZE, font)
        if stroke_data is None:
            pytest.fail(f"Failed to generate stroke data for '{character}' in {font}")

        # Test each stroke's path alignment
        for i, stroke in enumerate(stroke_data["strokes"]):
            points = stroke["points"]
            deviation = calculate_path_skeleton_deviation(points, skeleton, CANVAS_SIZE)

            # At least 80% of points should be within tolerance
            min_percent = 80.0
            assert deviation["percent_within_tolerance"] >= min_percent, (
                f"Path alignment poor for '{character}' stroke {i+1} in {font}:\n"
                f"  Only {deviation['percent_within_tolerance']:.1f}% of points within tolerance "
                f"(need {min_percent}%)\n"
                f"  Avg distance: {deviation['avg_distance']:.1f}, "
                f"Max distance: {deviation['max_distance']:.1f}\n"
                f"  Tolerance: {self.path_tolerance:.1f}\n"
                f"  Students following this guide would be penalized!"
            )

    @pytest.mark.parametrize("font", FONTS_TO_TEST)
    @pytest.mark.parametrize("character", UPPERCASE)
    def test_uppercase_start_end_alignment(self, font: str, character: str):
        """Test that uppercase stroke start/end points are near skeleton."""
        self._test_start_end_alignment(character, font)

    @pytest.mark.parametrize("font", FONTS_TO_TEST)
    @pytest.mark.parametrize("character", LOWERCASE)
    def test_lowercase_start_end_alignment(self, font: str, character: str):
        """Test that lowercase stroke start/end points are near skeleton."""
        self._test_start_end_alignment(character, font)

    @pytest.mark.parametrize("font", FONTS_TO_TEST)
    @pytest.mark.parametrize("character", DIGITS)
    def test_digit_start_end_alignment(self, font: str, character: str):
        """Test that digit stroke start/end points are near skeleton."""
        self._test_start_end_alignment(character, font)

    def _test_start_end_alignment(self, character: str, font: str):
        """Test that stroke start and end points are close to skeleton."""
        # Skip if no stroke data
        json_data = get_character_strokes(character, font)
        if json_data is None:
            pytest.skip(f"No stroke data for '{character}' in {font}")

        # Get skeleton
        skeleton = get_skeleton_pixels(character, CANVAS_SIZE, font)
        if not skeleton.any():
            pytest.skip(f"Empty skeleton for '{character}' in {font}")

        # Get guided strokes
        stroke_data = generate_hybrid_stroke_data(character, CANVAS_SIZE, font)
        if stroke_data is None:
            pytest.fail(f"Failed to generate stroke data for '{character}' in {font}")

        # Test each stroke's start and end points
        for i, stroke in enumerate(stroke_data["strokes"]):
            points = stroke["points"]
            if len(points) < 2:
                continue

            start_point = (points[0][0], points[0][1])
            end_point = (points[-1][0], points[-1][1])

            start_dist = point_to_skeleton_distance(start_point, skeleton, CANVAS_SIZE)
            end_dist = point_to_skeleton_distance(end_point, skeleton, CANVAS_SIZE)

            assert start_dist <= self.start_end_tolerance, (
                f"Start point too far from skeleton for '{character}' stroke {i+1} in {font}:\n"
                f"  Start point: ({start_point[0]:.1f}, {start_point[1]:.1f})\n"
                f"  Distance to skeleton: {start_dist:.1f} (tolerance: {self.start_end_tolerance:.1f})\n"
                f"  Students starting here would fail validation!"
            )

            assert end_dist <= self.start_end_tolerance, (
                f"End point too far from skeleton for '{character}' stroke {i+1} in {font}:\n"
                f"  End point: ({end_point[0]:.1f}, {end_point[1]:.1f})\n"
                f"  Distance to skeleton: {end_dist:.1f} (tolerance: {self.start_end_tolerance:.1f})\n"
                f"  Students ending here would fail validation!"
            )


class TestTraceSkeletonAlignment:
    """Test that trace images use the font skeleton correctly."""

    @pytest.mark.parametrize("font", FONTS_TO_TEST)
    @pytest.mark.parametrize("character", UPPERCASE[:5])  # Test subset for speed
    def test_trace_image_generated(self, font: str, character: str):
        """Test that trace image can be generated from skeleton."""
        from app.services.trace_generator import generate_trace_image

        # Get skeleton to verify it exists
        skeleton = get_skeleton_pixels(character, CANVAS_SIZE, font)
        if not skeleton.any():
            pytest.skip(f"Empty skeleton for '{character}' in {font}")

        # Generate trace image - should not fail
        trace_image = generate_trace_image(character, CANVAS_SIZE, font)

        # Trace image should be a non-empty base64 string
        assert trace_image, f"Failed to generate trace image for '{character}' in {font}"
        assert len(trace_image) > 100, f"Trace image too small for '{character}' in {font}"

    @pytest.mark.parametrize("font", FONTS_TO_TEST)
    @pytest.mark.parametrize("character", UPPERCASE[:5])
    def test_step_by_step_matches_skeleton_bounds(self, font: str, character: str):
        """Test that step-by-step guides align with skeleton bounds."""
        from app.services.font_strokes import get_character_strokes

        # Skip if no stroke data
        json_data = get_character_strokes(character, font)
        if json_data is None:
            pytest.skip(f"No stroke data for '{character}' in {font}")

        # Get skeleton bounds
        skeleton = get_skeleton_pixels(character, CANVAS_SIZE, font)
        if not skeleton.any():
            pytest.skip(f"Empty skeleton for '{character}' in {font}")

        skeleton_coords = np.argwhere(skeleton)
        skel_min_y, skel_min_x = skeleton_coords.min(axis=0)
        skel_max_y, skel_max_x = skeleton_coords.max(axis=0)

        # Get hybrid stroke data (what students actually see)
        stroke_data = generate_hybrid_stroke_data(character, CANVAS_SIZE, font)
        if not stroke_data:
            pytest.fail(f"Failed to generate stroke data for '{character}' in {font}")

        # Get stroke bounds in pixel space
        all_points = []
        for stroke in stroke_data["strokes"]:
            for p in stroke["points"]:
                all_points.append((p[0] * CANVAS_SIZE / 100, p[1] * CANVAS_SIZE / 100))

        if not all_points:
            pytest.fail(f"No stroke points for '{character}' in {font}")

        stroke_min_x = min(p[0] for p in all_points)
        stroke_max_x = max(p[0] for p in all_points)
        stroke_min_y = min(p[1] for p in all_points)
        stroke_max_y = max(p[1] for p in all_points)

        # Stroke bounds should be within 10% of skeleton bounds
        tolerance = CANVAS_SIZE * 0.10

        assert abs(skel_min_x - stroke_min_x) <= tolerance, (
            f"Stroke X start mismatch for '{character}' in {font}: "
            f"skeleton={skel_min_x}, stroke={stroke_min_x:.0f}"
        )
        assert abs(skel_max_x - stroke_max_x) <= tolerance, (
            f"Stroke X end mismatch for '{character}' in {font}: "
            f"skeleton={skel_max_x}, stroke={stroke_max_x:.0f}"
        )


class TestStrokeCountConsistency:
    """Test that stroke counts are consistent and reasonable."""

    @pytest.mark.parametrize("font", FONTS_TO_TEST)
    @pytest.mark.parametrize("character", UPPERCASE + LOWERCASE + DIGITS)
    def test_stroke_count_matches_json(self, font: str, character: str):
        """Test that generated strokes match JSON stroke count."""
        json_data = get_character_strokes(character, font)
        if json_data is None:
            pytest.skip(f"No stroke data for '{character}' in {font}")

        json_stroke_count = len(json_data.get("strokes", []))

        stroke_data = generate_hybrid_stroke_data(character, CANVAS_SIZE, font)
        if stroke_data is None:
            pytest.fail(f"Failed to generate stroke data for '{character}' in {font}")

        generated_count = stroke_data["stroke_count"]

        assert generated_count == json_stroke_count, (
            f"Stroke count mismatch for '{character}' in {font}: "
            f"JSON has {json_stroke_count}, generated {generated_count}"
        )

    @pytest.mark.parametrize("font", FONTS_TO_TEST)
    @pytest.mark.parametrize("character", UPPERCASE + LOWERCASE + DIGITS)
    def test_strokes_have_sufficient_points(self, font: str, character: str):
        """Test that each stroke has enough points for smooth rendering."""
        json_data = get_character_strokes(character, font)
        if json_data is None:
            pytest.skip(f"No stroke data for '{character}' in {font}")

        stroke_data = generate_hybrid_stroke_data(character, CANVAS_SIZE, font)
        if stroke_data is None:
            pytest.fail(f"Failed to generate stroke data for '{character}' in {font}")

        min_points_straight = 20  # Minimum for straight strokes
        min_points_curved = 40   # Minimum for curved strokes

        for i, stroke in enumerate(stroke_data["strokes"]):
            points = stroke["points"]
            curvature = stroke.get("curvature", "straight")

            if curvature in ["curved", "complex"]:
                min_required = min_points_curved
            else:
                min_required = min_points_straight

            assert len(points) >= min_required, (
                f"Stroke {i+1} for '{character}' in {font} has too few points: "
                f"{len(points)} (need {min_required} for {curvature} stroke)"
            )


def run_alignment_report():
    """Generate a detailed alignment report (can be run standalone)."""
    print("\n" + "=" * 70)
    print("STROKE ALIGNMENT REPORT")
    print("=" * 70)

    results = []

    for font in FONTS_TO_TEST:
        print(f"\n{font}:")
        print("-" * 50)

        for char in UPPERCASE + LOWERCASE + DIGITS:
            json_data = get_character_strokes(char, font)
            if json_data is None:
                continue

            skeleton_bounds = get_skeleton_bounds(char, CANVAS_SIZE, font)
            if skeleton_bounds is None:
                continue

            stroke_data = generate_hybrid_stroke_data(char, CANVAS_SIZE, font)
            if stroke_data is None:
                continue

            # Calculate bounds
            all_points = []
            for stroke in stroke_data["strokes"]:
                all_points.extend(stroke["points"])

            if not all_points:
                continue

            stroke_bounds = (
                min(p[0] for p in all_points),
                min(p[1] for p in all_points),
                max(p[0] for p in all_points),
                max(p[1] for p in all_points)
            )

            deviation = calculate_bounds_deviation(skeleton_bounds, stroke_bounds)

            status = "OK" if deviation["max_diff"] <= 5 else "WARN" if deviation["max_diff"] <= 10 else "FAIL"

            results.append({
                "char": char,
                "font": font,
                "deviation": deviation["max_diff"],
                "status": status
            })

            if status != "OK":
                print(f"  '{char}': {status} - max deviation {deviation['max_diff']:.1f}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    ok_count = sum(1 for r in results if r["status"] == "OK")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")

    print(f"  OK:   {ok_count}")
    print(f"  WARN: {warn_count}")
    print(f"  FAIL: {fail_count}")
    print(f"  Total: {len(results)}")

    if fail_count > 0:
        print("\nFailed characters need attention - students would be penalized!")


if __name__ == "__main__":
    run_alignment_report()
