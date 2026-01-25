"""Scoring service for evaluating drawn characters against reference images."""

import base64
import io
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_dilation, distance_transform_edt
from skimage.morphology import medial_axis
from skimage.transform import resize  # pylint: disable=no-name-in-module


def generate_reference_image(character: str, size: int = 200, font_name: Optional[str] = None) -> Image.Image:
    """Generate a reference image for a character using the specified font"""
    import os

    img = Image.new("L", (size, size), color=255)
    draw = ImageDraw.Draw(img)

    font_size = int(size * 0.75)
    font = None

    # Map font names to file names
    font_file_map = {
        "Fredoka-Regular": "Fredoka-Regular.ttf",
        "Nunito-Regular": "Nunito-Regular.ttf",
        "PlaywriteUS-Regular": "PlaywriteUS-Regular.ttf",
        "PatrickHand-Regular": "PatrickHand-Regular.ttf",
        "Schoolbell-Regular": "Schoolbell-Regular.ttf",
    }

    # Get the font file name (default to Fredoka)
    font_file = font_file_map.get(font_name or "", "Fredoka-Regular.ttf")

    # Build path to bundled font
    fonts_dir = os.path.join(os.path.dirname(__file__), "..", "fonts")
    bundled_font = os.path.abspath(os.path.join(fonts_dir, font_file))

    font_paths = [
        bundled_font,
        # Fallback to Fredoka if specified font not found
        os.path.abspath(os.path.join(fonts_dir, "Fredoka-Regular.ttf")),
        # System fallbacks
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]

    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except OSError:
            continue

    if font is None:
        font = ImageFont.load_default()  # type: ignore[assignment]

    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), character, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1]

    draw.text((x, y), character, fill=0, font=font)

    return img


def extract_and_center_character(image: Image.Image, target_size: int = 128, padding: float = 0.1) -> np.ndarray:
    """
    Extract the drawn character, center it, and normalize to target size.
    This ensures that size and position on the canvas don't affect scoring.
    """
    # Convert to grayscale if needed
    if image.mode != "L":
        image = image.convert("L")

    img_array = np.array(image)

    # Find the bounding box of the drawn content (dark pixels)
    # Threshold to find drawn pixels (assuming dark drawing on light background)
    threshold = 200  # Pixels darker than this are considered drawn
    drawn_mask = img_array < threshold

    if not np.any(drawn_mask):
        # No drawing detected, return empty normalized array
        return np.ones((target_size, target_size))

    # Find bounding box of drawn content
    rows = np.any(drawn_mask, axis=1)
    cols = np.any(drawn_mask, axis=0)
    row_min, row_max = np.where(rows)[0][[0, -1]]
    col_min, col_max = np.where(cols)[0][[0, -1]]

    # Extract the character region
    char_region = img_array[row_min : row_max + 1, col_min : col_max + 1]

    # Calculate the size to fit within target with padding
    char_height, char_width = char_region.shape
    available_size = int(target_size * (1 - 2 * padding))

    # Scale to fit while maintaining aspect ratio
    scale = min(available_size / char_width, available_size / char_height)
    new_width = max(1, int(char_width * scale))
    new_height = max(1, int(char_height * scale))

    # Resize the character region
    char_resized = resize(char_region, (new_height, new_width), anti_aliasing=True)

    # Create centered output image (white background)
    output = np.ones((target_size, target_size))

    # Calculate position to center the character
    y_offset = (target_size - new_height) // 2
    x_offset = (target_size - new_width) // 2

    # Place the resized character in the center
    output[y_offset : y_offset + new_height, x_offset : x_offset + new_width] = char_resized

    # Normalize to 0-1 range
    output_normalized = (output - output.min()) / (output.max() - output.min() + 1e-8)

    return output_normalized


def preprocess_image(image: Image.Image, target_size: int = 128) -> np.ndarray:
    """Preprocess image for comparison (legacy function for reference images)"""
    # Convert to grayscale if needed
    if image.mode != "L":
        image = image.convert("L")

    # Convert to numpy array
    img_array = np.array(image)

    # Resize to standard size
    img_resized = resize(img_array, (target_size, target_size), anti_aliasing=True)

    # Normalize
    img_normalized = (img_resized - img_resized.min()) / (img_resized.max() - img_resized.min() + 1e-8)

    return img_normalized


def find_endpoints(skeleton: np.ndarray) -> list:
    """Find all endpoint coordinates in a skeleton (pixels with exactly 1 neighbor)."""
    neighbor_count = np.zeros_like(skeleton, dtype=int)
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dy == 0 and dx == 0:
                continue
            shifted = np.roll(np.roll(skeleton, dy, axis=0), dx, axis=1)
            neighbor_count += shifted.astype(int)

    endpoint_mask = skeleton & (neighbor_count == 1)
    return list(zip(*np.where(endpoint_mask)))


def bridge_gaps(skeleton: np.ndarray, max_gap: int = 6) -> np.ndarray:
    """
    Bridge small gaps between nearly-connected strokes.
    If an endpoint is within max_gap pixels of another stroke, connect them.
    """
    from skimage.draw import line  # pylint: disable=no-name-in-module,import-outside-toplevel

    result = skeleton.copy()
    endpoints = find_endpoints(skeleton)

    if len(endpoints) < 2:
        return result

    # For each endpoint, find if there's another part of the skeleton nearby
    # that it could connect to (but isn't already connected)
    for ey, ex in endpoints:
        # Check if this endpoint is still an endpoint (might have been connected)
        neighbor_count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue
                ny, nx = ey + dy, ex + dx
                if 0 <= ny < result.shape[0] and 0 <= nx < result.shape[1]:
                    if result[ny, nx]:
                        neighbor_count += 1

        if neighbor_count != 1:
            continue  # No longer an endpoint

        # Look for skeleton pixels within max_gap that aren't directly connected
        best_target = None
        best_dist = max_gap + 1

        for dy in range(-max_gap, max_gap + 1):
            for dx in range(-max_gap, max_gap + 1):
                if dy == 0 and dx == 0:
                    continue

                ty, tx = ey + dy, ex + dx

                # Check bounds
                if not (0 <= ty < result.shape[0] and 0 <= tx < result.shape[1]):
                    continue

                # Skip if not a skeleton pixel
                if not result[ty, tx]:
                    continue

                # Calculate distance
                dist = np.sqrt(dy * dy + dx * dx)
                if dist > max_gap:
                    continue

                # Check if this pixel is already connected to our endpoint
                # by checking if removing our endpoint disconnects it
                # Simple check: is it a direct neighbor?
                if abs(dy) <= 1 and abs(dx) <= 1:
                    continue  # Already a neighbor

                # Check if there's a path between them already (within a small area)
                # Simple heuristic: check if they're on different "branches"
                # by seeing if the target is an endpoint or junction
                target_neighbors = 0
                for ddy in [-1, 0, 1]:
                    for ddx in [-1, 0, 1]:
                        if ddy == 0 and ddx == 0:
                            continue
                        nny, nnx = ty + ddy, tx + ddx
                        if 0 <= nny < result.shape[0] and 0 <= nnx < result.shape[1]:
                            if result[nny, nnx]:
                                target_neighbors += 1

                # Prefer connecting to other endpoints or junction points
                if dist < best_dist:
                    best_dist = dist
                    best_target = (ty, tx)

        # If we found a nearby target, draw a line to connect them
        if best_target is not None:
            rr, cc = line(ey, ex, best_target[0], best_target[1])
            # Only draw if all points are in bounds
            if np.all(rr >= 0) and np.all(rr < result.shape[0]) and np.all(cc >= 0) and np.all(cc < result.shape[1]):
                result[rr, cc] = True

    return result


def sand_drawing(binary_img: np.ndarray, prune_length: int = 8, bridge_gap: int = 10) -> np.ndarray:
    """
    "Sand" the drawing to remove minor imperfections like overshoots and small protrusions,
    while also bridging small gaps where strokes almost connect.

    This is like light sanding to clip minor edges without changing the main shape,
    plus a bit of "glue" to connect nearly-touching strokes.

    Steps:
    1. Use medial_axis for smoother centerlines than skeletonize
    2. Bridge small gaps between nearly-connected endpoints
    3. Prune short branches that represent overshoots (with over-pruning protection)
    """
    if not np.any(binary_img):
        return binary_img

    # Use medial_axis for smoother centerlines than skeletonize
    skeleton, _ = medial_axis(binary_img, return_distance=True)

    # First, bridge small gaps between nearly-connected strokes
    bridged = bridge_gaps(skeleton, max_gap=bridge_gap)

    # Calculate initial stroke pixels for over-pruning protection
    initial_pixels = np.sum(bridged)
    max_removal = int(initial_pixels * 0.15)  # Max 15% removal limit
    total_removed = 0

    # Then prune short branches by finding and removing endpoints iteratively
    pruned = bridged.copy()

    for _ in range(prune_length):
        # Check if we've hit the removal limit
        if total_removed >= max_removal:
            break

        # Find endpoints (pixels with only 1 neighbor)
        neighbor_count = np.zeros_like(pruned, dtype=int)
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue
                shifted = np.roll(np.roll(pruned, dy, axis=0), dx, axis=1)
                neighbor_count += shifted.astype(int)

        # Endpoints have exactly 1 neighbor
        endpoints = pruned & (neighbor_count == 1)
        num_endpoints = np.sum(endpoints)

        if num_endpoints == 0:
            break

        # Check if removing all endpoints would exceed limit
        if total_removed + num_endpoints > max_removal:
            # Only remove some endpoints to stay within limit
            remaining_budget = max_removal - total_removed
            if remaining_budget <= 0:
                break
            # Remove endpoints until we hit the budget
            endpoint_coords = list(zip(*np.where(endpoints)))
            endpoints_to_remove = np.zeros_like(endpoints)
            for i, (y, x) in enumerate(endpoint_coords):
                if i >= remaining_budget:
                    break
                endpoints_to_remove[y, x] = True
            endpoints = endpoints_to_remove
            num_endpoints = remaining_budget

        # Remove endpoints
        pruned = pruned & ~endpoints
        total_removed += num_endpoints

    return pruned


def normalize_line_thickness(
    binary_img: np.ndarray, target_thickness: int = 5, apply_sanding: bool = True
) -> np.ndarray:
    """
    Normalize line thickness using medial axis for smoother centerlines,
    then use distance transform for smooth stroke reconstruction.
    This ensures thin and thick drawings are compared fairly.

    If apply_sanding is True, also removes minor overshoots and protrusions.
    """
    if not np.any(binary_img):
        return binary_img

    # Optionally sand the drawing first to remove minor imperfections
    if apply_sanding:
        skeleton = sand_drawing(binary_img, prune_length=8, bridge_gap=10)
    else:
        # Use medial_axis for smoother centerlines than skeletonize
        skeleton, _ = medial_axis(binary_img, return_distance=True)

    # Use distance transform for smooth stroke reconstruction
    # instead of binary dilation which creates blocky results
    if target_thickness > 1:
        # Get distance from each pixel to nearest skeleton pixel
        if not np.any(skeleton):
            return binary_img
        skeleton_dist = distance_transform_edt(~skeleton)
        # Create smooth stroke by thresholding distance
        normalized = skeleton_dist <= (target_thickness / 2)
    else:
        normalized = skeleton

    return normalized


def calculate_coverage_score(drawn_img: np.ndarray, reference_img: np.ndarray, tolerance: int = 4) -> float:
    """
    Calculate how much of the reference character is covered by the drawing.
    Uses tolerance-based coverage that forgives slight misalignments.

    A reference pixel counts as "covered" if any drawn pixel is within tolerance distance.
    """
    # Threshold images to binary
    drawn_binary = drawn_img < 0.5
    reference_binary = reference_img < 0.5

    # Normalize both with sanding for fair comparison
    drawn_normalized = normalize_line_thickness(drawn_binary, target_thickness=5, apply_sanding=True)
    reference_normalized = normalize_line_thickness(reference_binary, target_thickness=5, apply_sanding=False)

    if np.sum(reference_normalized) == 0:
        return 0.0

    if np.sum(drawn_normalized) == 0:
        return 0.0

    # Use distance transform for tolerance-based coverage
    # Distance from each pixel to nearest drawn pixel
    drawn_dist = distance_transform_edt(~drawn_normalized)

    # Reference pixel is "covered" if within tolerance distance of any drawn pixel
    covered = reference_normalized & (drawn_dist <= tolerance)

    coverage = np.sum(covered) / (np.sum(reference_normalized) + 1e-8)

    return min(coverage, 1.0)


def calculate_accuracy_score(drawn_img: np.ndarray, reference_img: np.ndarray) -> float:
    """Calculate how accurate the drawing is (staying on the lines)"""
    # Threshold images to binary
    drawn_binary = drawn_img < 0.5
    reference_binary = reference_img < 0.5

    # Normalize drawn with sanding (removes overshoots), reference without
    drawn_normalized = normalize_line_thickness(drawn_binary, target_thickness=5, apply_sanding=True)
    reference_normalized = normalize_line_thickness(reference_binary, target_thickness=5, apply_sanding=False)

    # Dilate reference slightly to allow for minor deviations (scaled for 128px)
    reference_zone = binary_dilation(reference_normalized, iterations=5)

    # Calculate how much of the drawing is within the acceptable zone
    if np.sum(drawn_normalized) == 0:
        return 0.0

    within_bounds = np.logical_and(drawn_normalized, reference_zone)
    accuracy = np.sum(within_bounds) / (np.sum(drawn_normalized) + 1e-8)

    return min(accuracy, 1.0)


def calculate_stroke_similarity(drawn_img: np.ndarray, reference_img: np.ndarray) -> float:
    """
    Calculate stroke-aware similarity using Chamfer distance + IoU.
    More appropriate for line drawings than SSIM.

    Returns 0-1 where 1 is perfect match.
    """
    # Threshold images to binary
    drawn_binary = drawn_img < 0.5
    reference_binary = reference_img < 0.5

    # Normalize both images with sanding for fair comparison
    drawn_norm = normalize_line_thickness(drawn_binary, target_thickness=5, apply_sanding=True)
    ref_norm = normalize_line_thickness(reference_binary, target_thickness=5, apply_sanding=False)

    # Handle edge cases
    drawn_pixels = np.sum(drawn_norm)
    ref_pixels = np.sum(ref_norm)

    if drawn_pixels == 0 or ref_pixels == 0:
        return 0.0

    # 1. IoU (Intersection over Union) - 40% weight
    intersection = np.sum(drawn_norm & ref_norm)
    union = np.sum(drawn_norm | ref_norm)
    iou = intersection / (union + 1e-8)

    # 2. Chamfer distance - 60% weight
    # Average distance from each drawn pixel to nearest reference pixel
    # and vice versa for symmetry

    # Distance from drawn pixels to reference
    ref_dist = distance_transform_edt(~ref_norm)
    drawn_to_ref = np.mean(ref_dist[drawn_norm]) if drawn_pixels > 0 else 0

    # Distance from reference pixels to drawn
    drawn_dist = distance_transform_edt(~drawn_norm)
    ref_to_drawn = np.mean(drawn_dist[ref_norm]) if ref_pixels > 0 else 0

    # Symmetric Chamfer distance (average of both directions)
    chamfer_dist = (drawn_to_ref + ref_to_drawn) / 2

    # Convert distance to similarity score (0-1)
    # Use a sigmoid-like function where distance of ~10 pixels gives ~0.5 similarity
    # At 128px resolution, max reasonable distance is ~64px
    max_dist = 20.0  # Distance at which similarity approaches 0
    chamfer_score = np.exp(-chamfer_dist / (max_dist / 3))

    # Combine IoU and Chamfer with weights
    similarity = iou * 0.4 + chamfer_score * 0.6

    return min(max(similarity, 0.0), 1.0)


def score_drawing(drawn_image_data: str, character: str, font_name: Optional[str] = None) -> dict:
    """
    Score a drawn character against the reference.

    Args:
        drawn_image_data: Base64 encoded image data (data URL or raw base64)
        character: The character that was supposed to be drawn
        font_name: The font to use for reference image (e.g., 'Fredoka-Regular')

    Returns:
        Dictionary with scores and reference image
    """
    # Parse the drawn image
    if "," in drawn_image_data:
        # Data URL format
        image_data = drawn_image_data.split(",")[1]
    else:
        image_data = drawn_image_data

    try:
        drawn_bytes = base64.b64decode(image_data)
        drawn_image = Image.open(io.BytesIO(drawn_bytes))
    except Exception as e:
        return {"error": f"Failed to decode image: {str(e)}"}

    # Generate reference image using specified font
    reference_image = generate_reference_image(character, size=200, font_name=font_name)

    # Preprocess images - extract and center the drawn character for fair comparison
    # This normalizes size and position so only shape quality matters
    drawn_processed = extract_and_center_character(drawn_image)
    reference_processed = extract_and_center_character(reference_image)

    # Calculate scores
    coverage = calculate_coverage_score(drawn_processed, reference_processed)
    accuracy = calculate_accuracy_score(drawn_processed, reference_processed)

    # Calculate stroke-aware similarity (replaces SSIM for better line comparison)
    try:
        similarity = calculate_stroke_similarity(drawn_processed, reference_processed)
    except Exception:
        similarity = 0.5

    # Combined score with rebalanced weights for better similarity influence
    combined_score = coverage * 0.35 + accuracy * 0.35 + similarity * 0.30

    # Convert to percentage (no artificial inflation needed since line thickness is normalized)
    percentage_score = int(min(100, combined_score * 100))
    percentage_score = min(100, max(0, percentage_score))

    # Generate star rating (1-5 stars) - thresholds adjusted to be achievable for kids
    if percentage_score >= 80:
        stars = 5
        feedback = "Amazing! Perfect!"
    elif percentage_score >= 65:
        stars = 4
        feedback = "Great job!"
    elif percentage_score >= 50:
        stars = 3
        feedback = "Good work!"
    elif percentage_score >= 30:
        stars = 2
        feedback = "Nice try!"
    else:
        stars = 1
        feedback = "Keep practicing!"

    # Convert reference image to base64 for response
    ref_buffer = io.BytesIO()
    reference_image.save(ref_buffer, format="PNG")
    ref_base64 = base64.b64encode(ref_buffer.getvalue()).decode("utf-8")

    # Generate debug images showing normalized versions
    def array_to_base64(arr: np.ndarray) -> str:
        # Convert normalized array (0-1, where dark=low) to image
        img_data = ((1 - arr) * 255).astype(np.uint8)  # Invert so strokes are black
        img = Image.fromarray(img_data, mode="L")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    # Get the normalized versions for debug display
    drawn_binary = drawn_processed < 0.5
    reference_binary = reference_processed < 0.5

    # Show both unsanded and sanded versions for comparison
    drawn_unsanded = normalize_line_thickness(drawn_binary, target_thickness=5, apply_sanding=False)
    drawn_sanded = normalize_line_thickness(drawn_binary, target_thickness=5, apply_sanding=True)
    reference_normalized = normalize_line_thickness(reference_binary, target_thickness=5, apply_sanding=False)

    return {
        "score": percentage_score,
        "stars": stars,
        "feedback": feedback,
        "details": {
            "coverage": round(coverage * 100, 1),
            "accuracy": round(accuracy * 100, 1),
            "similarity": round(similarity * 100, 1),
        },
        "reference_image": f"data:image/png;base64,{ref_base64}",
        "debug": {
            "drawn_unsanded": f"data:image/png;base64,{array_to_base64(drawn_unsanded.astype(float))}",
            "drawn_sanded": f"data:image/png;base64,{array_to_base64(drawn_sanded.astype(float))}",
            "reference_normalized": f"data:image/png;base64,{array_to_base64(reference_normalized.astype(float))}",
            "drawn_centered": f"data:image/png;base64,{array_to_base64(drawn_processed)}",
            "reference_centered": f"data:image/png;base64,{array_to_base64(reference_processed)}",
        },
    }
