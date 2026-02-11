"""
Stroke Path Generator Service

Generates accurate stroke paths from font skeleton while preserving pedagogical metadata
(stroke order, directions, instructions) from JSON files. This creates a hybrid system
where curves always match the actual font rendering.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.services.font_strokes import get_character_strokes
from app.services.trace_generator import (
    extract_stroke_paths,
    generate_character_image,
    skeletonize,
)


def extract_high_resolution_paths(
    character: str, size: int = 400, font_name: Optional[str] = None, min_point_spacing: float = 2.0
) -> List[List[Tuple[float, float]]]:
    """
    Extract high-resolution stroke paths from font skeleton with minimal simplification.

    Args:
        character: The character to extract paths for
        size: Canvas size in pixels
        font_name: Optional font name
        min_point_spacing: Minimum distance between consecutive points

    Returns:
        List of paths, each path is a list of (x, y) tuples
    """
    # Generate character image
    char_img = generate_character_image(character, size, font_name)

    # Convert to binary
    binary = char_img < 128

    # Skeletonize
    skeleton = skeletonize(binary)

    # Extract raw paths with small minimum length to catch all strokes
    raw_paths = extract_stroke_paths(skeleton, min_length=8)

    # Apply minimal simplification - just remove points too close together
    simplified_paths = []
    for path in raw_paths:
        if len(path) < 2:
            continue

        simplified = [path[0]]
        for point in path[1:]:
            last = simplified[-1]
            dist = math.sqrt((point[0] - last[0]) ** 2 + (point[1] - last[1]) ** 2)
            if dist >= min_point_spacing:
                simplified.append(point)

        # Always include the last point
        if simplified[-1] != path[-1]:
            simplified.append(path[-1])

        if len(simplified) >= 2:
            simplified_paths.append(simplified)

    return simplified_paths


def calculate_path_distance(path1: List[Tuple[float, float]], path2: List[List[float]]) -> float:
    """
    Calculate the average distance between two paths by sampling points.
    Lower distance = more similar paths.
    """
    if not path1 or not path2:
        return float('inf')

    # Convert path2 to tuples if needed
    path2_tuples = [(p[0], p[1]) for p in path2]

    # Sample points from both paths
    def sample_path(path, num_samples=10):
        if len(path) <= num_samples:
            return list(path)
        step = (len(path) - 1) / (num_samples - 1)
        return [path[int(i * step)] for i in range(num_samples)]

    samples1 = sample_path(path1)
    samples2 = sample_path(path2_tuples)

    # Calculate average minimum distance from samples1 to samples2
    total_dist = 0
    for p1 in samples1:
        min_dist = float('inf')
        for p2 in samples2:
            dist = math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
            min_dist = min(min_dist, dist)
        total_dist += min_dist

    return total_dist / len(samples1)


def match_endpoint_region(
    point: Tuple[float, float],
    region_center: List[float],
    tolerance: float
) -> bool:
    """Check if a point is within tolerance of a region center."""
    dist = math.sqrt(
        (point[0] - region_center[0]) ** 2 +
        (point[1] - region_center[1]) ** 2
    )
    return dist <= tolerance


def merge_connected_paths(
    paths: List[List[Tuple[float, float]]],
    connection_tolerance: float = 5.0
) -> List[List[Tuple[float, float]]]:
    """
    Merge skeleton paths that are connected (endpoints within tolerance).
    This handles fragmented skeletons where a single stroke is split into parts.
    """
    if len(paths) <= 1:
        return paths

    # Create a list of paths we can modify
    remaining = [list(p) for p in paths]
    merged = []

    while remaining:
        current = remaining.pop(0)

        # Keep trying to extend current path
        changed = True
        while changed:
            changed = False
            current_start = current[0]
            current_end = current[-1]

            for i, other in enumerate(remaining):
                if not other:
                    continue

                other_start = other[0]
                other_end = other[-1]

                # Check if other's start connects to current's end
                dist_end_to_start = math.sqrt(
                    (current_end[0] - other_start[0]) ** 2 +
                    (current_end[1] - other_start[1]) ** 2
                )
                if dist_end_to_start <= connection_tolerance:
                    # Append other to current (skip duplicate point)
                    current = current + other[1:]
                    remaining[i] = []
                    changed = True
                    break

                # Check if other's end connects to current's start
                dist_start_to_end = math.sqrt(
                    (current_start[0] - other_end[0]) ** 2 +
                    (current_start[1] - other_end[1]) ** 2
                )
                if dist_start_to_end <= connection_tolerance:
                    # Prepend other to current (skip duplicate point)
                    current = other[:-1] + current
                    remaining[i] = []
                    changed = True
                    break

                # Check if other's end connects to current's end (reverse other)
                dist_end_to_end = math.sqrt(
                    (current_end[0] - other_end[0]) ** 2 +
                    (current_end[1] - other_end[1]) ** 2
                )
                if dist_end_to_end <= connection_tolerance:
                    # Append reversed other to current
                    current = current + list(reversed(other))[1:]
                    remaining[i] = []
                    changed = True
                    break

                # Check if other's start connects to current's start (reverse other)
                dist_start_to_start = math.sqrt(
                    (current_start[0] - other_start[0]) ** 2 +
                    (current_start[1] - other_start[1]) ** 2
                )
                if dist_start_to_start <= connection_tolerance:
                    # Prepend reversed other to current
                    current = list(reversed(other))[:-1] + current
                    remaining[i] = []
                    changed = True
                    break

            # Clean up empty paths
            remaining = [p for p in remaining if p]

        merged.append(current)

    return merged


def get_path_bounding_box(
    paths: List[List[Tuple[float, float]]]
) -> Tuple[float, float, float, float]:
    """Get bounding box of all paths (min_x, min_y, max_x, max_y)."""
    all_x = []
    all_y = []
    for path in paths:
        for point in path:
            all_x.append(point[0])
            all_y.append(point[1])
    if not all_x:
        return (0, 0, 100, 100)
    return (min(all_x), min(all_y), max(all_x), max(all_y))


def normalize_paths_to_bounds(
    paths: List[List[Tuple[float, float]]],
    source_bounds: Tuple[float, float, float, float],
    target_bounds: Tuple[float, float, float, float]
) -> List[List[Tuple[float, float]]]:
    """
    Normalize paths from source bounds to target bounds.
    This aligns the character position regardless of where it renders on the canvas.
    """
    s_min_x, s_min_y, s_max_x, s_max_y = source_bounds
    t_min_x, t_min_y, t_max_x, t_max_y = target_bounds

    s_width = s_max_x - s_min_x or 1
    s_height = s_max_y - s_min_y or 1
    t_width = t_max_x - t_min_x or 1
    t_height = t_max_y - t_min_y or 1

    normalized = []
    for path in paths:
        new_path = []
        for point in path:
            # Map from source bounds to target bounds
            norm_x = (point[0] - s_min_x) / s_width
            norm_y = (point[1] - s_min_y) / s_height
            new_x = t_min_x + norm_x * t_width
            new_y = t_min_y + norm_y * t_height
            new_path.append((new_x, new_y))
        normalized.append(new_path)

    return normalized


def is_straight_path(path: List[List[float]], tolerance: float = 5.0) -> bool:
    """Check if a path is essentially a straight line."""
    if len(path) <= 2:
        return True

    # Check deviation from straight line between first and last points
    start = path[0]
    end = path[-1]
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.sqrt(dx * dx + dy * dy)

    if length < 1:
        return True

    # Check each intermediate point's distance from the line
    for point in path[1:-1]:
        # Distance from point to line
        cross = abs((point[0] - start[0]) * dy - (point[1] - start[1]) * dx)
        dist = cross / length
        if dist > tolerance:
            return False

    return True


def collect_skeleton_points_along_path(
    skeleton_paths: List[List[Tuple[float, float]]],
    guide_path: List[List[float]],
    corridor_width: float = 30.0
) -> List[Tuple[float, float]]:
    """
    Collect skeleton points that fall within a corridor around the guide path.
    This handles fragmented skeletons by gathering all nearby points.

    Args:
        skeleton_paths: All skeleton paths
        guide_path: The JSON-defined path to follow (scaled to canvas coordinates)
        corridor_width: Half-width of corridor around the path

    Returns:
        List of skeleton points ordered along the guide path
    """
    # Use narrower corridor for straight paths to avoid picking up nearby curves
    is_straight = is_straight_path(guide_path)
    effective_corridor = corridor_width * 0.3 if is_straight else corridor_width

    def point_to_path_distance(px: float, py: float, path: List[List[float]]) -> Tuple[float, float]:
        """Calculate distance from point to path and position along path (0-1)."""
        min_dist = float('inf')
        best_t = 0

        total_length = 0
        segment_lengths = []
        for i in range(len(path) - 1):
            dx = path[i + 1][0] - path[i][0]
            dy = path[i + 1][1] - path[i][1]
            length = math.sqrt(dx * dx + dy * dy)
            segment_lengths.append(length)
            total_length += length

        if total_length == 0:
            return (0, 0)

        cumulative = 0
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            dx = x2 - x1
            dy = y2 - y1
            seg_len = segment_lengths[i]

            if seg_len == 0:
                dist = math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
                t = cumulative / total_length
            else:
                # Project point onto segment
                t_seg = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (seg_len * seg_len)))
                proj_x = x1 + t_seg * dx
                proj_y = y1 + t_seg * dy
                dist = math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)
                t = (cumulative + t_seg * seg_len) / total_length

            if dist < min_dist:
                min_dist = dist
                best_t = t

            cumulative += seg_len

        return (min_dist, best_t)

    # Collect all skeleton points with their distance and position
    collected = []
    for path in skeleton_paths:
        for point in path:
            dist, t = point_to_path_distance(point[0], point[1], guide_path)
            if dist <= effective_corridor:
                collected.append((point, t, dist))

    if not collected:
        return []

    # Sort by position along the path
    collected.sort(key=lambda x: x[1])

    # For straight paths, filter out outliers that deviate from the median position
    if is_straight and len(collected) > 3:
        # Determine if primarily vertical or horizontal
        start = guide_path[0]
        end = guide_path[-1]
        is_vertical = abs(end[1] - start[1]) > abs(end[0] - start[0])

        if is_vertical:
            # For vertical lines, filter by X coordinate
            x_coords = [c[0][0] for c in collected]
            median_x = sorted(x_coords)[len(x_coords) // 2]
            max_deviation = effective_corridor * 0.5
            collected = [c for c in collected if abs(c[0][0] - median_x) <= max_deviation]
        else:
            # For horizontal lines, filter by Y coordinate
            y_coords = [c[0][1] for c in collected]
            median_y = sorted(y_coords)[len(y_coords) // 2]
            max_deviation = effective_corridor * 0.5
            collected = [c for c in collected if abs(c[0][1] - median_y) <= max_deviation]

    # Return just the points
    return [c[0] for c in collected]


def match_skeleton_to_metadata(
    skeleton_paths: List[List[Tuple[float, float]]],
    json_strokes: List[Dict[str, Any]],
    size: int = 400,
    tolerance_percent: float = 0.25
) -> List[Dict[str, Any]]:
    """
    Match skeleton paths to JSON stroke metadata using start/end region matching.
    Normalizes both skeleton and JSON paths to the same coordinate space
    to handle different character positioning.

    Args:
        skeleton_paths: High-resolution paths extracted from skeleton
        json_strokes: Stroke definitions from JSON with metadata
        size: Canvas size (used to scale JSON points from 0-100 space)
        tolerance_percent: Tolerance as percentage of character size for matching endpoints

    Returns:
        List of hybrid strokes with skeleton paths and JSON metadata
    """
    scale = size / 100.0

    # Merge connected skeleton paths (handles fragmented skeletons)
    merged_skeleton = merge_connected_paths(skeleton_paths, connection_tolerance=10.0)

    # Get bounding box of skeleton paths
    skeleton_bounds = get_path_bounding_box(merged_skeleton)

    # Get bounding box of JSON strokes (in canvas-scaled coordinates)
    json_points_flat = []
    for stroke in json_strokes:
        for p in stroke["points"]:
            json_points_flat.append((p[0] * scale, p[1] * scale))
    json_bounds = get_path_bounding_box([json_points_flat]) if json_points_flat else (0, 0, size, size)

    # Normalize merged skeleton paths to match JSON bounding box
    # This aligns the character regardless of where it renders
    normalized_skeleton = normalize_paths_to_bounds(
        merged_skeleton, skeleton_bounds, json_bounds
    )

    # Calculate tolerance based on character size (not canvas size)
    char_size = max(
        json_bounds[2] - json_bounds[0],
        json_bounds[3] - json_bounds[1]
    )
    tolerance = char_size * tolerance_percent

    # Scale JSON stroke points to canvas size
    scaled_json_strokes = []
    for stroke in json_strokes:
        scaled_points = [[p[0] * scale, p[1] * scale] for p in stroke["points"]]
        scaled_json_strokes.append({
            **stroke,
            "scaled_points": scaled_points
        })

    # For each JSON stroke, collect skeleton points along the path
    # This handles fragmented skeletons by gathering all nearby points
    corridor_width = char_size * 0.15  # 15% of character size

    matched_strokes = []
    for json_stroke in scaled_json_strokes:
        guide_path = json_stroke["scaled_points"]

        # Collect skeleton points along this stroke's corridor
        collected_points = collect_skeleton_points_along_path(
            normalized_skeleton, guide_path, corridor_width
        )

        if len(collected_points) >= 3:
            # Remove duplicate/very close points
            filtered_points = [collected_points[0]]
            for pt in collected_points[1:]:
                last = filtered_points[-1]
                dist = math.sqrt((pt[0] - last[0]) ** 2 + (pt[1] - last[1]) ** 2)
                if dist >= 2.0:  # Minimum 2 pixel spacing
                    filtered_points.append(pt)

            # Ensure we have the endpoint
            if filtered_points and collected_points:
                last_collected = collected_points[-1]
                last_filtered = filtered_points[-1]
                if last_collected != last_filtered:
                    filtered_points.append(last_collected)

            if len(filtered_points) >= 2:
                # Convert from canvas coordinates to normalized 0-100 space
                normalized_path = [[p[0] * 100 / size, p[1] * 100 / size] for p in filtered_points]

                matched_strokes.append({
                    "points": normalized_path,
                    "direction": json_stroke.get("direction", "down"),
                    "original_points": json_stroke["points"],
                    "matched": True
                })
                continue

        # Fallback: try to find a matching skeleton path by endpoint
        best_match_idx = None
        best_match_score = float('inf')
        best_match_reversed = False

        json_start = json_stroke["scaled_points"][0]
        json_end = json_stroke["scaled_points"][-1]

        for i, skel_path in enumerate(normalized_skeleton):
            skel_start = skel_path[0]
            skel_end = skel_path[-1]

            # Try forward matching
            start_match_fwd = match_endpoint_region(skel_start, json_start, tolerance)
            end_match_fwd = match_endpoint_region(skel_end, json_end, tolerance)

            if start_match_fwd and end_match_fwd:
                score = calculate_path_distance(skel_path, json_stroke["scaled_points"])
                if score < best_match_score:
                    best_match_score = score
                    best_match_idx = i
                    best_match_reversed = False

            # Try reverse matching
            start_match_rev = match_endpoint_region(skel_end, json_start, tolerance)
            end_match_rev = match_endpoint_region(skel_start, json_end, tolerance)

            if start_match_rev and end_match_rev:
                score = calculate_path_distance(list(reversed(skel_path)), json_stroke["scaled_points"])
                if score < best_match_score:
                    best_match_score = score
                    best_match_idx = i
                    best_match_reversed = True

        if best_match_idx is not None:
            skel_path = normalized_skeleton[best_match_idx]
            if best_match_reversed:
                skel_path = list(reversed(skel_path))

            normalized_path = [[p[0] * 100 / size, p[1] * 100 / size] for p in skel_path]

            matched_strokes.append({
                "points": normalized_path,
                "direction": json_stroke.get("direction", "down"),
                "original_points": json_stroke["points"],
                "matched": True
            })
        else:
            # No skeleton match - use original JSON points (fallback)
            matched_strokes.append({
                "points": json_stroke["points"],
                "direction": json_stroke.get("direction", "down"),
                "original_points": json_stroke["points"],
                "matched": False
            })

    return matched_strokes


def interpolate_path_smooth(
    points: List[List[float]],
    num_points: int = 50
) -> List[List[float]]:
    """
    Interpolate a path to have more points using Catmull-Rom spline for smooth curves.

    Args:
        points: Original path points
        num_points: Desired number of output points

    Returns:
        Smoothly interpolated path with more points
    """
    if len(points) < 2:
        return points

    if len(points) == 2:
        # Linear interpolation for 2 points
        result = []
        for i in range(num_points):
            t = i / (num_points - 1)
            x = points[0][0] + t * (points[1][0] - points[0][0])
            y = points[0][1] + t * (points[1][1] - points[0][1])
            result.append([x, y])
        return result

    # Catmull-Rom spline interpolation
    def catmull_rom(p0, p1, p2, p3, t):
        """Calculate point on Catmull-Rom spline at parameter t."""
        t2 = t * t
        t3 = t2 * t

        x = 0.5 * ((2 * p1[0]) +
                   (-p0[0] + p2[0]) * t +
                   (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                   (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)

        y = 0.5 * ((2 * p1[1]) +
                   (-p0[1] + p2[1]) * t +
                   (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                   (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)

        return [x, y]

    result = []
    n = len(points)

    # Calculate total path length to distribute points evenly
    total_length = 0
    for i in range(n - 1):
        dx = points[i + 1][0] - points[i][0]
        dy = points[i + 1][1] - points[i][1]
        total_length += math.sqrt(dx * dx + dy * dy)

    points_per_segment = max(2, num_points // (n - 1))

    for i in range(n - 1):
        # Control points for Catmull-Rom
        p0 = points[max(0, i - 1)]
        p1 = points[i]
        p2 = points[min(n - 1, i + 1)]
        p3 = points[min(n - 1, i + 2)]

        # Generate points for this segment
        for j in range(points_per_segment):
            if i == n - 2 and j == points_per_segment - 1:
                # Last point
                result.append(list(points[-1]))
            elif i > 0 and j == 0:
                # Skip first point of non-first segments (already added)
                continue
            else:
                t = j / points_per_segment
                result.append(catmull_rom(p0, p1, p2, p3, t))

    # Ensure we end at the last point
    if result[-1] != list(points[-1]):
        result.append(list(points[-1]))

    return result


def classify_stroke_curvature(points: List[List[float]]) -> str:
    """
    Classify whether a stroke is straight, curved, or complex.

    Returns:
        "straight", "curved", or "complex"
    """
    if len(points) < 3:
        return "straight"

    # Calculate the deviation from a straight line
    start = np.array(points[0])
    end = np.array(points[-1])
    line_vec = end - start
    line_length = np.linalg.norm(line_vec)

    if line_length < 1:
        return "straight"

    line_unit = line_vec / line_length

    max_deviation = 0
    total_deviation = 0

    for point in points[1:-1]:
        p = np.array(point)
        # Project point onto line
        t = np.dot(p - start, line_unit)
        projection = start + t * line_unit
        deviation = np.linalg.norm(p - projection)
        max_deviation = max(max_deviation, deviation)
        total_deviation += deviation

    avg_deviation = total_deviation / max(1, len(points) - 2)
    relative_deviation = max_deviation / line_length

    if relative_deviation < 0.05:
        return "straight"
    elif relative_deviation < 0.25:
        return "curved"
    else:
        return "complex"


def infer_stroke_direction(points: List[List[float]]) -> str:
    """
    Infer the drawing direction from the path geometry.
    Returns a direction string like 'down', 'right', 'curve-left', etc.
    """
    if len(points) < 2:
        return "down"

    start = points[0]
    end = points[-1]
    dx = end[0] - start[0]
    dy = end[1] - start[1]

    # Check if it's a closed loop (oval)
    dist_start_end = math.sqrt(dx * dx + dy * dy)
    if dist_start_end < 5:  # Start and end are very close
        return "oval"

    # Check for curvature
    curvature = classify_stroke_curvature(points)

    # Determine primary direction
    abs_dx = abs(dx)
    abs_dy = abs(dy)

    if curvature == "complex":
        # Check for S-curve pattern
        if abs_dy > abs_dx * 2:
            return "s-curve"
        return "curve"

    if curvature == "curved":
        if abs_dx > abs_dy:
            if dx > 0:
                return "curve-right"
            else:
                return "curve-left"
        else:
            if dy > 0:
                return "curve-down" if dx >= 0 else "down-curve"
            else:
                return "curve-up"

    # Straight or nearly straight
    if abs_dy > abs_dx * 2:  # Mostly vertical
        return "down" if dy > 0 else "up"
    elif abs_dx > abs_dy * 2:  # Mostly horizontal
        return "right" if dx > 0 else "left"
    else:  # Diagonal
        if dy > 0:
            return "down-right" if dx > 0 else "down-left"
        else:
            return "up-right" if dx > 0 else "up-left"


def get_skeleton_bounds(character: str, size: int, font_name: Optional[str]) -> Optional[Tuple[float, float, float, float]]:
    """
    Get the bounding box of the character's skeleton in 0-100 normalized space.
    Returns (min_x, min_y, max_x, max_y) or None if extraction fails.
    """
    from skimage.morphology import skeletonize as sk_skeletonize

    char_img = generate_character_image(character, size, font_name)
    binary = char_img < 128
    skeleton = sk_skeletonize(binary)

    coords = np.argwhere(skeleton)
    if len(coords) == 0:
        return None

    min_y, min_x = coords.min(axis=0)
    max_y, max_x = coords.max(axis=0)

    # Convert to 0-100 space
    scale = 100.0 / size
    return (min_x * scale, min_y * scale, max_x * scale, max_y * scale)


def normalize_stroke_to_skeleton(
    points: List[List[float]],
    json_bounds: Tuple[float, float, float, float],
    skeleton_bounds: Tuple[float, float, float, float]
) -> List[List[float]]:
    """
    Transform stroke points from JSON coordinate space to match skeleton bounds.
    This aligns the JSON-defined shapes with the actual font rendering.

    Handles edge cases:
    - Single-width dimensions (vertical/horizontal lines): centers within skeleton
    - Preserves aspect ratio when possible
    """
    j_min_x, j_min_y, j_max_x, j_max_y = json_bounds
    s_min_x, s_min_y, s_max_x, s_max_y = skeleton_bounds

    j_width = j_max_x - j_min_x
    j_height = j_max_y - j_min_y
    s_width = s_max_x - s_min_x
    s_height = s_max_y - s_min_y

    # Handle zero-width or zero-height cases (single line)
    if j_width < 0.001:  # Vertical line
        j_width = 1
        j_center_x = j_min_x
    else:
        j_center_x = (j_min_x + j_max_x) / 2

    if j_height < 0.001:  # Horizontal line
        j_height = 1
        j_center_y = j_min_y
    else:
        j_center_y = (j_min_y + j_max_y) / 2

    s_center_x = (s_min_x + s_max_x) / 2
    s_center_y = (s_min_y + s_max_y) / 2

    # Calculate scale factors
    scale_x = s_width / j_width if j_width > 0.001 else 1
    scale_y = s_height / j_height if j_height > 0.001 else 1

    normalized = []
    for p in points:
        # For single-line dimensions, center within skeleton bounds
        if j_max_x - j_min_x < 0.001:
            # Vertical line - center X within skeleton
            new_x = s_center_x
        else:
            # Scale X normally
            new_x = s_min_x + (p[0] - j_min_x) * scale_x

        if j_max_y - j_min_y < 0.001:
            # Horizontal line - center Y within skeleton
            new_y = s_center_y
        else:
            # Scale Y normally
            new_y = s_min_y + (p[1] - j_min_y) * scale_y

        normalized.append([new_x, new_y])

    return normalized


def generate_hybrid_stroke_data(
    character: str,
    size: int = 400,
    font_name: Optional[str] = None,
    use_interpolation: bool = True,
    target_points: int = 60
) -> Optional[Dict[str, Any]]:
    """
    Generate stroke data from JSON stroke definitions, normalized to match the
    actual font skeleton, with smooth curve interpolation.

    The JSON defines the correct stroke shapes and order. We normalize the coordinates
    to match where the font actually renders, then apply Catmull-Rom spline
    interpolation for smooth curves.

    Args:
        character: The character to generate data for
        size: Canvas size in pixels
        font_name: Optional font name
        use_interpolation: Whether to smooth interpolate the paths
        target_points: Target number of points per stroke if interpolating

    Returns:
        Dict with stroke data, or None if character not found
    """
    # Get JSON stroke definitions (pedagogically correct stroke order and shapes)
    json_data = get_character_strokes(character, font_name)
    if json_data is None:
        return None

    json_strokes = json_data.get("strokes", [])
    if not json_strokes:
        return None

    # Get skeleton bounds to normalize JSON coordinates
    skeleton_bounds = get_skeleton_bounds(character, size, font_name)

    # Calculate JSON bounds from all stroke points
    all_json_points = []
    for stroke in json_strokes:
        all_json_points.extend(stroke["points"])

    if all_json_points:
        json_bounds = (
            min(p[0] for p in all_json_points),
            min(p[1] for p in all_json_points),
            max(p[0] for p in all_json_points),
            max(p[1] for p in all_json_points)
        )
    else:
        json_bounds = (0, 0, 100, 100)

    # Build output strokes with normalization and smooth interpolation
    result_strokes = []
    for i, stroke in enumerate(json_strokes):
        points = stroke["points"]
        direction = stroke.get("direction", "down")

        # Normalize points to match skeleton bounds
        if skeleton_bounds:
            points = normalize_stroke_to_skeleton(points, json_bounds, skeleton_bounds)

        # Classify the stroke curvature
        curvature = classify_stroke_curvature(points)

        # Apply smooth interpolation to get many points for smooth rendering
        if use_interpolation and len(points) >= 2:
            # More points for complex curves, fewer for straight lines
            if curvature in ["curved", "complex"]:
                num_points = target_points * 2  # 120 points for curves
            else:
                num_points = target_points  # 60 points for straight lines
            points = interpolate_path_smooth(points, num_points)

        result_strokes.append({
            "points": points,
            "direction": direction,
            "curvature": curvature,
            "matched": True,
            "order": i + 1
        })

    return {
        "character": character,
        "font": font_name,
        "strokes": result_strokes,
        "stroke_count": len(result_strokes),
        "source": "json_normalized"
    }


def get_cached_hybrid_strokes(
    character: str,
    size: int = 400,
    font_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get hybrid stroke data, using cache when available.

    This function integrates with the guide_cache system for persistence.
    """
    # For now, generate on-the-fly
    # TODO: Integrate with guide_cache.py for persistent caching
    return generate_hybrid_stroke_data(character, size, font_name)
