"""
Word image generation service using ComfyUI.
Generates kid-friendly clipart-style images for vocabulary words.
"""

import os
import shutil
import subprocess  # nosec B404 - Used for vtracer SVG conversion with controlled inputs
import time
from typing import Optional

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from app.services.audio_generator import CHARACTER_DATA

# Load environment variables
load_dotenv()

# Directory for word images
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "words")
REGULAR_DIR = os.path.join(IMAGES_DIR, "regular")
HIGH_CONTRAST_DIR = os.path.join(IMAGES_DIR, "high-contrast")

# ComfyUI API settings
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
COMFYUI_USERNAME = os.getenv("COMFYUI_USERNAME", "")
COMFYUI_PASSWORD = os.getenv("COMFYUI_PASSWORD", "")
COMFYUI_OUTPUT_DIR = os.getenv("COMFYUI_OUTPUT_DIR", os.path.expanduser("~/projects/comfy/ComfyUI/output"))


def get_comfyui_auth() -> Optional[HTTPBasicAuth]:
    """Get basic auth for ComfyUI if credentials are configured."""
    if COMFYUI_USERNAME and COMFYUI_PASSWORD:
        return HTTPBasicAuth(COMFYUI_USERNAME, COMFYUI_PASSWORD)
    return None

# Model to use - hassakuXLIllustrious is great for illustrations
CHECKPOINT_MODEL = "hassakuXLIllustrious_v33.safetensors"

# Prompt templates for consistent style
# Using green background for easy removal with rembg
REGULAR_PROMPT = (
    "simple flat vector illustration of {word}, kid-friendly cartoon style, "
    "colorful, centered, solid bright green background, clean lines, clipart, "
    "no text, no words, single object, cute, friendly, high quality, "
    "digital art, simple shapes"
)

HIGH_CONTRAST_PROMPT = (
    "simple flat vector illustration of {word}, kid-friendly cartoon style, "
    "bold primary colors red blue yellow, thick black outlines, high contrast, centered, "
    "solid bright green background, clean lines, clipart, no text, no words, single object, "
    "simple shapes, bold colors"
)

# Negative prompt to avoid unwanted elements
NEGATIVE_PROMPT = (
    "text, words, letters, numbers, watermark, signature, "
    "realistic, photographic, blurry, low quality, multiple objects, "
    "complex background, gradient, human, person, face, hands"
)


def get_all_unique_words() -> list[str]:
    """Extract all unique words from CHARACTER_DATA."""
    words = set()
    for char_data in CHARACTER_DATA.values():
        for word in char_data.get("words", []):
            # Normalize: lowercase, replace spaces with underscores for filenames
            words.add(word.lower())
    return sorted(list(words))


def get_word_filename(word: str) -> str:
    """Convert word to safe filename."""
    # Replace spaces and special chars with underscores
    safe_name = word.lower().replace(" ", "_").replace("-", "_")
    # Remove any remaining unsafe characters
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
    return safe_name


def get_word_image_path(word: str, high_contrast: bool = False) -> Optional[str]:
    """Get the path to a word's image file."""
    filename = get_word_filename(word)
    directory = HIGH_CONTRAST_DIR if high_contrast else REGULAR_DIR

    # Check for SVG first, then PNG
    svg_path = os.path.join(directory, f"{filename}.svg")
    png_path = os.path.join(directory, f"{filename}.png")

    if os.path.exists(svg_path):
        return svg_path
    if os.path.exists(png_path):
        return png_path
    return None


def get_word_image_url(word: str, high_contrast: bool = False) -> Optional[str]:
    """Get the URL path to a word's image."""
    filename = get_word_filename(word)
    variant = "high-contrast" if high_contrast else "regular"

    # Check if file exists
    svg_path = os.path.join(HIGH_CONTRAST_DIR if high_contrast else REGULAR_DIR, f"{filename}.svg")
    png_path = os.path.join(HIGH_CONTRAST_DIR if high_contrast else REGULAR_DIR, f"{filename}.png")

    if os.path.exists(svg_path):
        return f"/static/words/{variant}/{filename}.svg"
    if os.path.exists(png_path):
        return f"/static/words/{variant}/{filename}.png"
    return None


def check_comfyui_available() -> bool:
    """Check if ComfyUI is running and accessible."""
    try:
        response = requests.get(f"{COMFYUI_URL}/system_stats", timeout=5, auth=get_comfyui_auth())
        return response.status_code == 200
    except requests.RequestException:
        return False


def create_sdxl_workflow(prompt: str, negative_prompt: str, filename: str) -> dict:
    """Create a ComfyUI workflow for SDXL image generation using hassakuXLIllustrious."""
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CHECKPOINT_MODEL}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": prompt}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": negative_prompt}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"batch_size": 1, "height": 512, "width": 512}},
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "cfg": 7,
                "denoise": 1,
                "latent_image": ["4", 0],
                "model": ["1", 0],
                "negative": ["3", 0],
                "positive": ["2", 0],
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "seed": int(time.time() * 1000) % (2**32),
                "steps": 25,
            },
        },
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename, "images": ["6", 0]}},
    }


def remove_background(input_path: str, output_path: str) -> bool:
    """Remove background from image using rembg."""
    try:
        from rembg import remove

        with open(input_path, "rb") as inp:
            input_data = inp.read()

        output_data = remove(input_data)

        # Save as PNG with transparency
        with open(output_path, "wb") as out:
            out.write(output_data)

        return True
    except Exception as e:
        print(f"Background removal failed: {e}")
        return False


def queue_prompt(workflow: dict) -> Optional[str]:
    """Queue a prompt in ComfyUI and return the prompt ID."""
    try:
        response = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=30, auth=get_comfyui_auth())
        if response.status_code == 200:
            return response.json().get("prompt_id")
    except requests.RequestException as e:
        print(f"Error queuing prompt: {e}")
    return None


def wait_for_completion(prompt_id: str, timeout: int = 120) -> bool:
    """Wait for a prompt to complete."""
    start_time = time.time()
    auth = get_comfyui_auth()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10, auth=auth)
            if response.status_code == 200:
                history = response.json()
                if prompt_id in history:
                    return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


def convert_png_to_svg(png_path: str, svg_path: str) -> bool:
    """Convert PNG to SVG using vtracer."""
    try:
        # vtracer must be installed: cargo install vtracer
        # nosec B603, B607 - Paths are internally generated and controlled
        result = subprocess.run(  # nosec
            [
                "vtracer",
                "--input",
                png_path,
                "--output",
                svg_path,
                "--colormode",
                "color",
                "--hierarchical",
                "stacked",
                "--mode",
                "polygon",
                "--filter_speckle",
                "4",
                "--color_precision",
                "6",
                "--layer_difference",
                "16",
                "--corner_threshold",
                "60",
                "--length_threshold",
                "4.0",
                "--splice_threshold",
                "45",
                "--path_precision",
                "3",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"SVG conversion failed: {e}")
        return False


def generate_word_image(  # pragma: no cover
    word: str, high_contrast: bool = False, force: bool = False
) -> Optional[str]:
    """Generate an image for a word using ComfyUI with transparent background."""
    filename = get_word_filename(word)
    directory = HIGH_CONTRAST_DIR if high_contrast else REGULAR_DIR
    png_path = os.path.join(directory, f"{filename}.png")
    svg_path = os.path.join(directory, f"{filename}.svg")

    # Skip if already exists and not forcing
    if not force and (os.path.exists(png_path) or os.path.exists(svg_path)):
        print(f"Image already exists for '{word}'")
        return svg_path if os.path.exists(svg_path) else png_path

    if not check_comfyui_available():
        print("ComfyUI is not available")
        return None

    # Create prompt
    prompt_template = HIGH_CONTRAST_PROMPT if high_contrast else REGULAR_PROMPT
    prompt = prompt_template.format(word=word)

    # Create workflow
    workflow = create_sdxl_workflow(prompt, NEGATIVE_PROMPT, filename)

    # Queue and wait
    prompt_id = queue_prompt(workflow)
    if not prompt_id:
        print(f"Failed to queue prompt for '{word}'")
        return None

    print(f"Generating image for '{word}' (prompt_id: {prompt_id})...")
    if not wait_for_completion(prompt_id):
        print(f"Timeout waiting for '{word}'")
        return None

    # Find the generated PNG in ComfyUI output directory
    generated_files = [f for f in os.listdir(COMFYUI_OUTPUT_DIR) if f.startswith(filename) and f.endswith(".png")]

    if not generated_files:
        print(f"No output file found for '{word}'")
        return None

    # Get the most recent file
    source_path = os.path.join(COMFYUI_OUTPUT_DIR, sorted(generated_files)[-1])
    os.makedirs(directory, exist_ok=True)

    # Temporary file for raw image
    temp_path = os.path.join(directory, f"{filename}_raw.png")
    shutil.copy2(source_path, temp_path)

    # Remove background to create transparent PNG
    print(f"Removing background for '{word}'...")
    if remove_background(temp_path, png_path):
        print(f"Created transparent PNG for '{word}'")
        # Clean up temp file
        os.remove(temp_path)

        # Try to convert to SVG for scalability
        if convert_png_to_svg(png_path, svg_path):
            print(f"Converted to SVG for '{word}'")
            return svg_path
        print(f"SVG conversion failed, keeping PNG for '{word}'")
        return png_path
    # Fallback: keep raw image without transparency
    print(f"Background removal failed, keeping original for '{word}'")
    shutil.move(temp_path, png_path)
    return png_path


def generate_all_word_images(high_contrast: bool = False, force: bool = False) -> dict:  # pragma: no cover
    """Generate images for all unique words."""
    words = get_all_unique_words()
    results: dict[str, list[str]] = {"success": [], "failed": [], "skipped": []}

    for i, word in enumerate(words):
        print(f"\n[{i+1}/{len(words)}] Processing '{word}'...")

        # Check if already exists
        if not force and get_word_image_path(word, high_contrast):
            results["skipped"].append(word)
            continue

        path = generate_word_image(word, high_contrast, force)
        if path:
            results["success"].append(word)
        else:
            results["failed"].append(word)

        # Small delay to avoid overwhelming ComfyUI
        time.sleep(0.5)

    return results


def get_available_word_images() -> dict:
    """Get statistics about available word images."""
    all_words = get_all_unique_words()

    regular_available = []
    high_contrast_available = []
    missing = []

    for word in all_words:
        has_regular = get_word_image_path(word, False) is not None
        has_hc = get_word_image_path(word, True) is not None

        if has_regular:
            regular_available.append(word)
        if has_hc:
            high_contrast_available.append(word)
        if not has_regular and not has_hc:
            missing.append(word)

    return {
        "total_words": len(all_words),
        "regular_available": len(regular_available),
        "high_contrast_available": len(high_contrast_available),
        "missing": len(missing),
        "missing_words": missing,
        "all_words": all_words,
    }


# CLI for running generation
if __name__ == "__main__":  # pragma: no cover
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.services.word_images <command>")
        print("Commands:")
        print("  list          - List all unique words")
        print("  stats         - Show image availability statistics")
        print("  generate      - Generate all missing regular images")
        print("  generate-hc   - Generate all missing high-contrast images")
        print("  generate-all  - Generate both regular and high-contrast")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        words = get_all_unique_words()
        print(f"Total unique words: {len(words)}\n")
        for word in words:
            print(f"  - {word}")

    elif command == "stats":
        stats = get_available_word_images()
        print(f"Total words: {stats['total_words']}")
        print(f"Regular images available: {stats['regular_available']}")
        print(f"High-contrast images available: {stats['high_contrast_available']}")
        print(f"Missing images: {stats['missing']}")
        if stats["missing_words"]:
            print("\nMissing words:")
            for word in stats["missing_words"][:20]:
                print(f"  - {word}")
            if len(stats["missing_words"]) > 20:
                print(f"  ... and {len(stats['missing_words']) - 20} more")

    elif command == "generate":
        if not check_comfyui_available():
            print("Error: ComfyUI is not running or not accessible")
            print(f"Expected at: {COMFYUI_URL}")
            sys.exit(1)
        results = generate_all_word_images(high_contrast=False)
        success_count = len(results["success"])
        failed_count = len(results["failed"])
        skipped_count = len(results["skipped"])
        print(f"\nResults: {success_count} success, {failed_count} failed, {skipped_count} skipped")

    elif command == "generate-hc":
        if not check_comfyui_available():
            print("Error: ComfyUI is not running or not accessible")
            sys.exit(1)
        results = generate_all_word_images(high_contrast=True)
        success_count = len(results["success"])
        failed_count = len(results["failed"])
        skipped_count = len(results["skipped"])
        print(f"\nResults: {success_count} success, {failed_count} failed, {skipped_count} skipped")

    elif command == "generate-all":
        if not check_comfyui_available():
            print("Error: ComfyUI is not running or not accessible")
            sys.exit(1)
        print("Generating regular images...")
        results1 = generate_all_word_images(high_contrast=False)
        print("\nGenerating high-contrast images...")
        results2 = generate_all_word_images(high_contrast=True)
        print(f"\nRegular: {len(results1['success'])} success, {len(results1['failed'])} failed")
        print(f"High-contrast: {len(results2['success'])} success, {len(results2['failed'])} failed")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
