import base64
import io
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from skimage.metrics import structural_similarity as ssim
from skimage.transform import resize
from typing import Tuple


def generate_reference_image(character: str, size: int = 200) -> Image.Image:
    """Generate a reference image for a character"""
    img = Image.new('L', (size, size), color=255)
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fallback to default
    font_size = int(size * 0.75)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), character, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1]

    draw.text((x, y), character, fill=0, font=font)

    return img


def preprocess_image(image: Image.Image, target_size: int = 64) -> np.ndarray:
    """Preprocess image for comparison"""
    # Convert to grayscale if needed
    if image.mode != 'L':
        image = image.convert('L')

    # Convert to numpy array
    img_array = np.array(image)

    # Resize to standard size
    img_resized = resize(img_array, (target_size, target_size), anti_aliasing=True)

    # Normalize
    img_normalized = (img_resized - img_resized.min()) / (img_resized.max() - img_resized.min() + 1e-8)

    return img_normalized


def calculate_coverage_score(drawn_img: np.ndarray, reference_img: np.ndarray) -> float:
    """Calculate how much of the reference character is covered by the drawing"""
    # Threshold images to binary
    drawn_binary = drawn_img < 0.5  # Dark pixels are True
    reference_binary = reference_img < 0.5

    # Calculate overlap
    overlap = np.logical_and(drawn_binary, reference_binary)
    coverage = np.sum(overlap) / (np.sum(reference_binary) + 1e-8)

    return min(coverage, 1.0)


def calculate_accuracy_score(drawn_img: np.ndarray, reference_img: np.ndarray) -> float:
    """Calculate how accurate the drawing is (not going outside the lines)"""
    # Threshold images to binary
    drawn_binary = drawn_img < 0.5
    reference_binary = reference_img < 0.5

    # Dilate reference slightly to allow for some tolerance
    from scipy.ndimage import binary_dilation
    reference_dilated = binary_dilation(reference_binary, iterations=3)

    # Calculate how much of the drawing is within the dilated reference
    if np.sum(drawn_binary) == 0:
        return 0.0

    within_bounds = np.logical_and(drawn_binary, reference_dilated)
    accuracy = np.sum(within_bounds) / (np.sum(drawn_binary) + 1e-8)

    return min(accuracy, 1.0)


def score_drawing(drawn_image_data: str, character: str) -> dict:
    """
    Score a drawn character against the reference.

    Args:
        drawn_image_data: Base64 encoded image data (data URL or raw base64)
        character: The character that was supposed to be drawn

    Returns:
        Dictionary with scores and reference image
    """
    # Parse the drawn image
    if ',' in drawn_image_data:
        # Data URL format
        image_data = drawn_image_data.split(',')[1]
    else:
        image_data = drawn_image_data

    try:
        drawn_bytes = base64.b64decode(image_data)
        drawn_image = Image.open(io.BytesIO(drawn_bytes))
    except Exception as e:
        return {"error": f"Failed to decode image: {str(e)}"}

    # Generate reference image
    reference_image = generate_reference_image(character, size=200)

    # Preprocess both images
    drawn_processed = preprocess_image(drawn_image)
    reference_processed = preprocess_image(reference_image)

    # Calculate scores
    coverage = calculate_coverage_score(drawn_processed, reference_processed)
    accuracy = calculate_accuracy_score(drawn_processed, reference_processed)

    # Calculate SSIM for structural similarity
    try:
        similarity = ssim(drawn_processed, reference_processed, data_range=1.0)
        similarity = max(0, similarity)  # Ensure non-negative
    except Exception:
        similarity = 0.5

    # Combined score weighted towards coverage and accuracy
    combined_score = (coverage * 0.4 + accuracy * 0.4 + similarity * 0.2)

    # Convert to percentage and apply a curve to be more encouraging for kids
    # This makes scores generally higher while still rewarding good drawings
    percentage_score = int(min(100, combined_score * 100 * 1.2))
    percentage_score = min(100, max(0, percentage_score))

    # Generate star rating (1-5 stars)
    if percentage_score >= 90:
        stars = 5
        feedback = "Amazing! Perfect!"
    elif percentage_score >= 75:
        stars = 4
        feedback = "Great job!"
    elif percentage_score >= 60:
        stars = 3
        feedback = "Good work!"
    elif percentage_score >= 40:
        stars = 2
        feedback = "Nice try!"
    else:
        stars = 1
        feedback = "Keep practicing!"

    # Convert reference image to base64 for response
    ref_buffer = io.BytesIO()
    reference_image.save(ref_buffer, format='PNG')
    ref_base64 = base64.b64encode(ref_buffer.getvalue()).decode('utf-8')

    return {
        "score": percentage_score,
        "stars": stars,
        "feedback": feedback,
        "details": {
            "coverage": round(coverage * 100, 1),
            "accuracy": round(accuracy * 100, 1),
            "similarity": round(similarity * 100, 1)
        },
        "reference_image": f"data:image/png;base64,{ref_base64}"
    }
