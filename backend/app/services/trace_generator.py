"""Trace generator service for creating character stroke paths and trace images."""

import base64
import io
import os
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_dilation, label
from skimage.morphology import skeletonize


def get_font(size: int, font_name: Optional[str] = None):
    """Get font at specified size. If font_name is provided, use that font."""
    fonts_dir = os.path.join(os.path.dirname(__file__), "..", "fonts")
    fonts_dir = os.path.abspath(fonts_dir)

    font_paths = []

    if font_name:
        # Try to find the specified font
        if not font_name.endswith(".ttf"):
            font_name_with_ext = font_name + ".ttf"
        else:
            font_name_with_ext = font_name
        font_paths.append(os.path.join(fonts_dir, font_name_with_ext))

    # Default/fallback fonts
    font_paths.extend(
        [
            os.path.join(fonts_dir, "Fredoka-Regular.ttf"),
            "/usr/share/fonts/truetype/fredoka/Fredoka-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ]
    )

    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            continue

    return ImageFont.load_default()


def get_available_fonts() -> list:
    """Get list of available font names from the fonts directory"""
    fonts_dir = os.path.join(os.path.dirname(__file__), "..", "fonts")
    fonts_dir = os.path.abspath(fonts_dir)

    fonts = []
    if os.path.exists(fonts_dir):
        for f in os.listdir(fonts_dir):
            if f.endswith(".ttf"):
                # Return font name without extension
                fonts.append(f[:-4])

    return sorted(fonts)


def generate_character_image(character: str, size: int = 400, font_name: Optional[str] = None) -> np.ndarray:
    """Generate a binary image of the character"""
    img = Image.new("L", (size, size), color=255)
    draw = ImageDraw.Draw(img)

    font_size = int(size * 0.75)
    font = get_font(font_size, font_name)

    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), character, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1]

    draw.text((x, y), character, fill=0, font=font)

    return np.array(img)


def count_neighbors(skeleton: np.ndarray, y: int, x: int) -> int:
    """Count 8-connected neighbors of a skeleton point"""
    height, width = skeleton.shape
    count = 0
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dy == 0 and dx == 0:
                continue
            ny, nx = y + dy, x + dx
            if 0 <= ny < height and 0 <= nx < width and skeleton[ny, nx]:
                count += 1
    return count


def find_special_points(skeleton: np.ndarray) -> tuple:
    """
    Find endpoints (1 neighbor) and junction points (3+ neighbors) in skeleton.
    Returns (endpoints, junctions) as lists of (y, x) tuples.
    """
    height, width = skeleton.shape
    endpoints = []
    junctions = []

    for y in range(height):
        for x in range(width):
            if skeleton[y, x]:
                n = count_neighbors(skeleton, y, x)
                if n == 1:
                    endpoints.append((y, x))
                elif n >= 3:
                    junctions.append((y, x))

    return endpoints, junctions


def trace_path_to_special(skeleton: np.ndarray, start: tuple, visited_edges: set, special_points: set) -> list:
    """
    Trace a path from start point until reaching a junction, endpoint, or dead end.
    Uses visited_edges to avoid retracing the same edge twice.
    Returns list of (x, y) coordinates.
    """
    height, width = skeleton.shape
    neighbors_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    path = [(int(start[1]), int(start[0]))]  # Start with (x, y)
    current = start
    visited_local = {start}

    while True:
        y, x = current
        next_point = None

        for dy, dx in neighbors_offsets:
            ny, nx = y + dy, x + dx
            if 0 <= ny < height and 0 <= nx < width and skeleton[ny, nx]:
                if (ny, nx) in visited_local:
                    continue

                # Create edge key (sorted tuple of points)
                edge = tuple(sorted([(y, x), (ny, nx)]))
                if edge in visited_edges:
                    continue

                # Found a valid next point
                next_point = (ny, nx)
                visited_edges.add(edge)
                break

        if next_point is None:
            # No more unvisited neighbors
            break

        path.append((int(next_point[1]), int(next_point[0])))  # (x, y)
        visited_local.add(next_point)
        current = next_point

        # Stop if we hit a junction or endpoint (special point)
        if next_point in special_points and next_point != start:
            break

    return path


def extract_stroke_paths(skeleton: np.ndarray, min_length: int = 10) -> list:
    """
    Extract individual stroke paths from skeleton, handling junctions properly.
    Each stroke goes from endpoint/junction to another endpoint/junction.
    Returns list of paths, each path is a list of (x, y) coordinates.
    """
    # Find connected components
    labeled, num_features = label(skeleton)
    all_paths = []

    for i in range(1, num_features + 1):
        component = (labeled == i).astype(np.uint8)
        points = np.argwhere(component)

        if len(points) < min_length:
            continue

        # Find special points in this component
        endpoints, junctions = find_special_points(component)
        special_points = set(endpoints + junctions)

        # Track visited edges to avoid duplicates
        visited_edges: set[tuple] = set()

        # Start tracing from endpoints first (they have clear start points)
        start_points = endpoints + junctions

        # If no endpoints or junctions (closed loop), pick arbitrary start
        if not start_points:
            start_points = [(points[0][0], points[0][1])]

        for start in start_points:
            # Try tracing in all possible directions from this point
            height, width = component.shape
            neighbors_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

            for dy, dx in neighbors_offsets:
                ny, nx = start[0] + dy, start[1] + dx
                if 0 <= ny < height and 0 <= nx < width and component[ny, nx]:
                    edge = tuple(sorted([start, (ny, nx)]))
                    if edge not in visited_edges:
                        # Start a new path
                        path = trace_path_to_special(component, start, visited_edges, special_points)
                        if len(path) >= 2:
                            all_paths.append(path)

    # Filter paths by minimum length and deduplicate
    filtered_paths = [p for p in all_paths if len(p) >= min_length]
    filtered_paths = deduplicate_paths(filtered_paths)

    # Sort paths by starting y position (top to bottom)
    filtered_paths.sort(key=lambda p: p[0][1] if p else 0)

    return filtered_paths


def deduplicate_paths(paths: list) -> list:
    """
    Remove duplicate or highly overlapping paths.
    Two paths are considered duplicates if they share most of their points.
    """
    if not paths:
        return paths

    unique_paths: list[list] = []

    for path in paths:
        path_set = set(tuple(p) for p in path)

        is_duplicate = False
        path_to_remove = None
        for existing in list(unique_paths):  # Iterate over a copy
            existing_set = set(tuple(p) for p in existing)

            # Check overlap
            overlap = len(path_set & existing_set)
            min_len = min(len(path_set), len(existing_set))

            if min_len > 0 and overlap / min_len > 0.8:
                # More than 80% overlap - consider duplicate
                # Keep the longer path
                if len(path) > len(existing):
                    path_to_remove = existing
                is_duplicate = True
                break

        if path_to_remove is not None:
            unique_paths.remove(path_to_remove)
            unique_paths.append(path)
        elif not is_duplicate:
            unique_paths.append(path)

    return unique_paths


def simplify_path(path: list, tolerance: int = 3) -> list:
    """Simplify path by removing points that are too close together"""
    if len(path) < 2:
        return path

    simplified = [path[0]]

    for point in path[1:]:
        last = simplified[-1]
        dist = ((point[0] - last[0]) ** 2 + (point[1] - last[1]) ** 2) ** 0.5
        if dist >= tolerance:
            simplified.append(point)

    # Always include last point
    if simplified[-1] != path[-1]:
        simplified.append(path[-1])

    return simplified


def simplify_path_high_resolution(path: list, tolerance: float = 1.5) -> list:
    """
    Simplify path with minimal reduction for high-resolution output.
    Uses smaller tolerance to preserve curve details.
    """
    if len(path) < 2:
        return path

    simplified = [path[0]]

    for point in path[1:]:
        last = simplified[-1]
        dist = ((point[0] - last[0]) ** 2 + (point[1] - last[1]) ** 2) ** 0.5
        if dist >= tolerance:
            simplified.append(point)

    # Always include last point
    if simplified[-1] != path[-1]:
        simplified.append(path[-1])

    return simplified


def classify_path_curvature(path: list) -> str:
    """
    Classify a path as straight, curved, or complex based on deviation from straight line.

    Returns:
        "straight" - nearly linear path
        "curved" - single arc or gentle curve
        "complex" - S-curves, loops, or multiple direction changes
    """
    if len(path) < 3:
        return "straight"

    import numpy as np

    points = np.array(path)
    start = points[0]
    end = points[-1]
    line_vec = end - start
    line_length = np.linalg.norm(line_vec)

    if line_length < 1:
        return "straight"

    line_unit = line_vec / line_length

    # Calculate perpendicular deviation for each point
    deviations = []
    for point in points[1:-1]:
        t = np.dot(point - start, line_unit)
        projection = start + t * line_unit
        deviation = np.linalg.norm(point - projection)
        deviations.append(deviation)

    if not deviations:
        return "straight"

    max_deviation = max(deviations)
    avg_deviation = sum(deviations) / len(deviations)
    relative_deviation = max_deviation / line_length

    # Check for direction changes (sign changes in deviation from line)
    # This helps identify S-curves and complex shapes
    cross_products = []
    for point in points[1:-1]:
        vec_to_point = point - start
        cross = line_vec[0] * vec_to_point[1] - line_vec[1] * vec_to_point[0]
        cross_products.append(cross)

    direction_changes = 0
    for i in range(1, len(cross_products)):
        if cross_products[i] * cross_products[i - 1] < 0:
            direction_changes += 1

    if relative_deviation < 0.05:
        return "straight"
    elif direction_changes >= 2 or relative_deviation > 0.4:
        return "complex"
    else:
        return "curved"


def generate_high_resolution_guide_data(
    character: str, size: int = 400, font_name: Optional[str] = None
) -> dict:
    """
    Generate high-resolution stroke path data for smooth curve rendering.
    Uses minimal simplification to preserve curve details.

    Returns paths with many more points than generate_animated_guide_data(),
    suitable for smooth polyline rendering or bezier conversion.
    """
    # Generate character image
    char_img = generate_character_image(character, size, font_name)

    # Convert to binary
    binary = char_img < 128

    # Skeletonize
    skeleton = skeletonize(binary)

    # Extract stroke paths with lower minimum length
    raw_paths = extract_stroke_paths(skeleton, min_length=10)

    # Use high-resolution simplification (tolerance=1.5 instead of 4)
    paths = [simplify_path_high_resolution(path, tolerance=1.5) for path in raw_paths]

    strokes = []
    for i, path in enumerate(paths):
        if len(path) < 2:
            continue

        # Convert to percentage coordinates (0-100)
        normalized_path = [[p[0] * 100 / size, p[1] * 100 / size] for p in path]

        # Classify curvature
        curvature = classify_path_curvature(path)

        strokes.append({
            "points": normalized_path,
            "order": i + 1,
            "curvature": curvature,
            "point_count": len(normalized_path)
        })

    return {
        "character": character,
        "size": size,
        "strokes": strokes,
        "stroke_count": len(strokes),
        "high_resolution": True
    }


def merge_connected_stroke_paths(paths: list, tolerance: float = 3.0) -> list:
    """
    Merge stroke paths that are connected (endpoints within tolerance).
    This creates continuous strokes from fragments caused by skeleton junctions.
    """
    if len(paths) <= 1:
        return paths

    import math

    def distance(p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    # Keep merging until no more merges possible
    merged = [list(p) for p in paths]
    changed = True

    while changed:
        changed = False
        new_merged = []
        used = set()

        for i, path_i in enumerate(merged):
            if i in used:
                continue

            current = list(path_i)
            used.add(i)

            # Try to extend current path by finding connected paths
            extended = True
            while extended:
                extended = False
                for j, path_j in enumerate(merged):
                    if j in used:
                        continue

                    # Check all connection possibilities
                    if distance(current[-1], path_j[0]) <= tolerance:
                        # Append path_j to current
                        current = current + path_j[1:]
                        used.add(j)
                        extended = True
                        changed = True
                    elif distance(current[-1], path_j[-1]) <= tolerance:
                        # Append reversed path_j to current
                        current = current + list(reversed(path_j))[1:]
                        used.add(j)
                        extended = True
                        changed = True
                    elif distance(current[0], path_j[-1]) <= tolerance:
                        # Prepend path_j to current
                        current = path_j[:-1] + current
                        used.add(j)
                        extended = True
                        changed = True
                    elif distance(current[0], path_j[0]) <= tolerance:
                        # Prepend reversed path_j to current
                        current = list(reversed(path_j))[:-1] + current
                        used.add(j)
                        extended = True
                        changed = True

            new_merged.append(current)

        merged = new_merged

    return merged


def orient_stroke_for_writing(points: list) -> list:
    """
    Orient a stroke so it flows in a natural writing direction.
    - Vertical strokes: top to bottom
    - Horizontal strokes: left to right
    - Diagonal: top to bottom takes priority
    """
    if len(points) < 2:
        return points

    start = points[0]
    end = points[-1]
    dx = end[0] - start[0]
    dy = end[1] - start[1]

    # Determine if we should reverse
    should_reverse = False

    if abs(dy) > abs(dx):
        # Primarily vertical - should go top to bottom (increasing y)
        if dy < 0:
            should_reverse = True
    else:
        # Primarily horizontal - should go left to right (increasing x)
        if dx < 0:
            should_reverse = True

    if should_reverse:
        return list(reversed(points))
    return points


def order_strokes_for_writing(strokes: list) -> list:
    """
    Order strokes in a logical writing sequence and orient each stroke
    for natural drawing direction.
    Generally: top-to-bottom, left-to-right, with main strokes before details.
    """
    if not strokes:
        return strokes

    # First, orient each stroke for natural direction
    for stroke in strokes:
        stroke["points"] = orient_stroke_for_writing(stroke["points"])

    if len(strokes) <= 1:
        return strokes

    def stroke_bounds(stroke):
        pts = stroke["points"]
        if not pts:
            return (0, 0, 0, 0)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    # Sort by: top-most point, then left-most
    def sort_key(stroke):
        bounds = stroke_bounds(stroke)
        # Primary: top (min y), Secondary: left (min x)
        return (bounds[1], bounds[0])

    return sorted(strokes, key=sort_key)


def generate_animated_guide_data(character: str, size: int = 400, font_name: Optional[str] = None) -> dict:
    """
    Generate stroke path data for animated guide.
    Returns paths that can be animated on the frontend.

    Strokes are merged at junction points and ordered for logical writing sequence.
    """
    # Generate character image
    char_img = generate_character_image(character, size, font_name)

    # Convert to binary
    binary = char_img < 128

    # Skeletonize
    skeleton = skeletonize(binary)

    # Extract stroke paths - use lower min_length to capture curved segments
    raw_paths = extract_stroke_paths(skeleton, min_length=5)

    # Simplify paths for smoother animation - use lower tolerance for better curves
    paths = [simplify_path(path, tolerance=2) for path in raw_paths]

    # Merge connected paths to form complete strokes
    # Use larger tolerance to handle gaps from skeleton fragmentation at curves
    char_size = size * 0.6  # Approximate character size
    merge_tolerance = char_size * 0.20  # 20% of character size for aggressive merging
    merged_paths = merge_connected_stroke_paths(paths, tolerance=merge_tolerance)

    # Filter out noise paths - keep only substantial strokes
    # Use minimum length based on point count (not size) since paths are densely sampled
    min_path_length = 40  # Minimum 40 points for a valid stroke
    merged_paths = [p for p in merged_paths if len(p) >= min_path_length]

    # Define high-contrast colors for each stroke
    colors = [
        "#FF0000",  # Red
        "#00AA00",  # Green
        "#0000FF",  # Blue
        "#FF8800",  # Orange
        "#AA00AA",  # Purple
        "#00AAAA",  # Cyan
        "#FFAA00",  # Gold
        "#FF00AA",  # Pink
    ]

    strokes = []
    for i, path in enumerate(merged_paths):
        if len(path) < 2:
            continue

        # Convert to percentage coordinates (0-100)
        normalized_path = [[p[0] * 100 / size, p[1] * 100 / size] for p in path]

        strokes.append({"points": normalized_path, "color": colors[i % len(colors)], "order": i + 1})

    # Order strokes for logical writing sequence
    strokes = order_strokes_for_writing(strokes)

    # Re-assign order numbers after sorting
    for i, stroke in enumerate(strokes):
        stroke["order"] = i + 1

    return {"character": character, "size": size, "strokes": strokes, "stroke_count": len(strokes)}


def generate_trace_image(character: str, size: int = 400, font_name: Optional[str] = None) -> str:
    """
    Generate a dashed trace image from the font's skeleton.
    Returns base64 encoded PNG with transparent background.
    """
    # Generate character image
    char_img = generate_character_image(character, size, font_name)

    # Convert to binary
    binary = char_img < 128

    # Skeletonize
    skeleton = skeletonize(binary)

    # Dilate for visibility
    trace_line = binary_dilation(skeleton, iterations=3)

    # Create RGBA image
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = output.load()

    # Draw dashed line pattern
    skeleton_points = np.argwhere(trace_line)
    dash_on = True
    dash_counter = 0
    dash_length = 10
    gap_length = 6

    for y, x in skeleton_points:
        if dash_on:
            pixels[x, y] = (120, 120, 120, 200)  # Gray
        dash_counter += 1
        if dash_on and dash_counter >= dash_length:
            dash_on = False
            dash_counter = 0
        elif not dash_on and dash_counter >= gap_length:
            dash_on = True
            dash_counter = 0

    buffer = io.BytesIO()
    output.save(buffer, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"


def generate_all_guides(character: str, size: int = 400, font_name: Optional[str] = None) -> dict:
    """Generate all guide data for a character"""
    animated_data = generate_animated_guide_data(character, size, font_name)

    return {
        "character": character,
        "size": size,
        "font_name": font_name or "Fredoka-Regular",
        "trace_image": generate_trace_image(character, size, font_name),
        "animated_strokes": animated_data["strokes"],
        "stroke_count": animated_data["stroke_count"],
    }


def generate_font_preview(font_name: str, size: int = 600) -> str:
    """
    Generate a preview image showing all characters in the font.
    Returns base64 encoded PNG.
    """
    # Create image large enough for all characters
    img = Image.new("RGB", (size, size), color="white")
    draw = ImageDraw.Draw(img)

    font_size = int(size / 16)  # Smaller font to fit all chars
    font = get_font(font_size, font_name)

    # Characters to display
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lowercase = "abcdefghijklmnopqrstuvwxyz"
    numbers = "0123456789"

    # Draw title
    title_font = get_font(int(font_size * 0.8), font_name)
    draw.text((10, 10), f"Font: {font_name}", fill="#666", font=title_font)

    y_offset = int(size * 0.08)
    line_height = int(size * 0.12)

    # Draw uppercase (2 lines)
    draw.text((10, y_offset), uppercase[:13], fill="black", font=font)
    draw.text((10, y_offset + line_height), uppercase[13:], fill="black", font=font)

    # Draw lowercase (2 lines)
    y_offset += int(line_height * 2.5)
    draw.text((10, y_offset), lowercase[:13], fill="black", font=font)
    draw.text((10, y_offset + line_height), lowercase[13:], fill="black", font=font)

    # Draw numbers (1 line)
    y_offset += int(line_height * 2.5)
    draw.text((10, y_offset), numbers, fill="black", font=font)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
