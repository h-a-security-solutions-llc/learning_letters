#!/usr/bin/env python3
"""
Generate word images using ComfyUI.

This script generates kid-friendly clipart-style images for vocabulary words
using ComfyUI.

Usage:
    # Generate all missing word images
    python scripts/generate_word_images.py

    # Generate specific words (comma-separated)
    python scripts/generate_word_images.py apple,ball,cat

    # Force regenerate specific words (even if they exist)
    python scripts/generate_word_images.py --force apple,ball

    # Generate high-contrast versions
    python scripts/generate_word_images.py --high-contrast

    # List all words without generating
    python scripts/generate_word_images.py --list

    # Evaluate multiple models with a test word
    python scripts/generate_word_images.py --evaluate apple
"""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent.parent / ".env")

# Add parent directory to path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.audio_generator import CHARACTER_DATA  # noqa: E402

# Configuration
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://localhost:8188")
COMFYUI_OUTPUT_DIR = os.getenv("COMFYUI_OUTPUT_DIR", os.path.expanduser("~/projects/comfy/ComfyUI/output"))
COMFYUI_USERNAME = os.getenv("COMFYUI_USERNAME")
COMFYUI_PASSWORD = os.getenv("COMFYUI_PASSWORD")

# Create auth tuple if credentials are provided
COMFYUI_AUTH = (COMFYUI_USERNAME, COMFYUI_PASSWORD) if COMFYUI_USERNAME and COMFYUI_PASSWORD else None

# Output directories
SCRIPT_DIR = Path(__file__).parent
PENDING_REVIEW_DIR = SCRIPT_DIR / "pending_review"
EVAL_DIR = SCRIPT_DIR / "model_evaluation"
APPROVED_REGULAR_DIR = SCRIPT_DIR.parent / "app" / "static" / "words" / "regular"
APPROVED_HC_DIR = SCRIPT_DIR.parent / "app" / "static" / "words" / "high-contrast"

# Default model
DEFAULT_MODEL = "hassakuXLIllustrious_v33.safetensors"

# Models to evaluate (short name -> filename)
EVAL_MODELS = {
    "hassaku": "hassakuXLIllustrious_v33.safetensors",
    "sdxl_base": "sd_xl_base_1.0.safetensors",
    "dreamshaper": "dreamshaperXL_v21TurboDPMSDE.safetensors",
    "juggernaut": "juggernautXL_v9.safetensors",
}

# Prompt templates - simple and direct
REGULAR_PROMPT = "{word}, highly detailed"

HIGH_CONTRAST_PROMPT = "{word}, highly detailed, high contrast, bold colors"

NEGATIVE_PROMPT = "text, watermark, blurry, low quality"


def get_all_unique_words() -> list[str]:
    """Extract all unique words from CHARACTER_DATA."""
    words = set()
    for char_data in CHARACTER_DATA.values():
        for word in char_data.get("words", []):
            words.add(word.lower())
    return sorted(list(words))


def get_word_filename(word: str) -> str:
    """Convert word to safe filename."""
    safe_name = word.lower().replace(" ", "_").replace("-", "_")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
    return safe_name


def check_comfyui_available() -> bool:
    """Check if ComfyUI is running and accessible."""
    try:
        response = requests.get(f"{COMFYUI_URL}/system_stats", timeout=5, auth=COMFYUI_AUTH)
        return response.status_code == 200
    except requests.RequestException:
        return False


def create_workflow(prompt: str, negative_prompt: str, filename: str, model: str) -> dict:
    """Create a ComfyUI workflow for SDXL image generation."""
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": model},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": prompt},
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": negative_prompt},
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {"batch_size": 1, "height": 512, "width": 512},
        },
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
        "6": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["5", 0], "vae": ["1", 2]},
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": filename, "images": ["6", 0]},
        },
    }


def queue_prompt(workflow: dict) -> str | None:
    """Queue a prompt in ComfyUI and return the prompt ID."""
    try:
        response = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=30, auth=COMFYUI_AUTH)
        if response.status_code == 200:
            return response.json().get("prompt_id")
    except requests.RequestException as e:
        print(f"Error queuing prompt: {e}")
    return None


def wait_for_completion(prompt_id: str, timeout: int = 120) -> bool:
    """Wait for a prompt to complete."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10, auth=COMFYUI_AUTH)
            if response.status_code == 200:
                history = response.json()
                if prompt_id in history:
                    return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


def generate_with_model(word: str, model: str, output_filename: str, output_dir: Path) -> str | None:
    """Generate an image for a word using a specific model."""
    prompt = REGULAR_PROMPT.format(word=word)

    # Create and queue workflow
    workflow = create_workflow(prompt, NEGATIVE_PROMPT, output_filename, model)
    prompt_id = queue_prompt(workflow)

    if not prompt_id:
        print("    Failed to queue prompt")
        return None

    print(f"    Generating... (prompt_id: {prompt_id[:8]})")

    if not wait_for_completion(prompt_id, timeout=180):
        print("    Timeout waiting for generation")
        return None

    # Find the generated file in ComfyUI output
    comfyui_output = Path(COMFYUI_OUTPUT_DIR)
    generated_files = sorted(
        [f for f in comfyui_output.glob(f"{output_filename}*.png")],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )

    if not generated_files:
        print(f"    No output file found in {COMFYUI_OUTPUT_DIR}")
        return None

    source_file = generated_files[0]

    # Copy to output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    dest_path = output_dir / f"{output_filename}.png"
    shutil.copy2(source_file, dest_path)

    print(f"    Saved to: {dest_path.name}")
    return str(dest_path)


def evaluate_models(word: str) -> None:
    """Generate the same word with multiple models for comparison."""
    print(f"\nEvaluating models with word: '{word}'")
    print(f"Prompt: {REGULAR_PROMPT.format(word=word)}")
    print("=" * 50)

    results = {}

    for model_name, model_file in EVAL_MODELS.items():
        print(f"\n[{model_name}] Using model: {model_file}")

        # Check if model exists
        model_path = Path(COMFYUI_OUTPUT_DIR).parent / "models" / "checkpoints" / model_file
        if not model_path.exists():
            # Try alternate path
            model_path = Path.home() / "projects" / "comfy" / "ComfyUI" / "models" / "checkpoints" / model_file
            if not model_path.exists():
                print(f"    Model not found: {model_file}")
                results[model_name] = "NOT FOUND"
                continue

        output_filename = f"{get_word_filename(word)}_{model_name}"
        result = generate_with_model(word, model_file, output_filename, EVAL_DIR)

        if result:
            results[model_name] = "SUCCESS"
        else:
            results[model_name] = "FAILED"

        # Small delay between models
        time.sleep(2)

    print("\n" + "=" * 50)
    print("EVALUATION SUMMARY")
    print("=" * 50)
    for model_name, status in results.items():
        print(f"  {model_name}: {status}")
    print(f"\nReview images at: {EVAL_DIR}")


def generate_word_image(
    word: str, high_contrast: bool = False, force: bool = False, model: str = DEFAULT_MODEL
) -> str | None:
    """Generate an image for a word using ComfyUI."""
    filename = get_word_filename(word)
    variant = "hc" if high_contrast else "regular"
    output_filename = f"{filename}_{variant}"

    # Check if already in pending review
    pending_path = PENDING_REVIEW_DIR / f"{output_filename}.png"
    if pending_path.exists() and not force:
        print(f"  Already in pending review: {pending_path.name}")
        return str(pending_path)

    # Check if already approved
    approved_dir = APPROVED_HC_DIR if high_contrast else APPROVED_REGULAR_DIR
    for ext in [".svg", ".png"]:
        approved_path = approved_dir / f"{filename}{ext}"
        if approved_path.exists() and not force:
            print(f"  Already approved: {approved_path.name}")
            return str(approved_path)

    # Create prompt
    prompt_template = HIGH_CONTRAST_PROMPT if high_contrast else REGULAR_PROMPT
    prompt = prompt_template.format(word=word)

    # Create and queue workflow
    workflow = create_workflow(prompt, NEGATIVE_PROMPT, output_filename, model)
    prompt_id = queue_prompt(workflow)

    if not prompt_id:
        print("  Failed to queue prompt")
        return None

    print(f"  Generating... (prompt_id: {prompt_id[:8]})")

    if not wait_for_completion(prompt_id, timeout=180):
        print("  Timeout waiting for generation")
        return None

    # Find the generated file in ComfyUI output
    comfyui_output = Path(COMFYUI_OUTPUT_DIR)
    generated_files = sorted(
        [f for f in comfyui_output.glob(f"{output_filename}*.png")],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )

    if not generated_files:
        print(f"  No output file found in {COMFYUI_OUTPUT_DIR}")
        return None

    source_file = generated_files[0]

    # Move to pending review
    PENDING_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    dest_path = PENDING_REVIEW_DIR / f"{output_filename}.png"
    shutil.copy2(source_file, dest_path)

    print(f"  Saved to: {dest_path.name}")
    return str(dest_path)


def main():
    parser = argparse.ArgumentParser(description="Generate word images using ComfyUI")
    parser.add_argument(
        "words",
        nargs="?",
        help="Comma-separated list of words to generate (default: all)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force regenerate even if image exists",
    )
    parser.add_argument(
        "--high-contrast",
        "-hc",
        action="store_true",
        help="Generate high-contrast versions",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all words without generating",
    )
    parser.add_argument(
        "--delay",
        "-d",
        type=float,
        default=1.0,
        help="Delay between generations in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--evaluate",
        "-e",
        action="store_true",
        help="Evaluate multiple models with the specified word",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=DEFAULT_MODEL,
        help=f"Model to use for generation (default: {DEFAULT_MODEL})",
    )

    args = parser.parse_args()

    # Get word list
    all_words = get_all_unique_words()

    if args.list:
        print(f"Total unique words: {len(all_words)}\n")
        for word in all_words:
            print(f"  {word}")
        return

    # Check ComfyUI availability
    if not check_comfyui_available():
        print(f"Error: ComfyUI is not running at {COMFYUI_URL}")
        print("Please start ComfyUI and try again.")
        sys.exit(1)

    print(f"ComfyUI connected at {COMFYUI_URL}")

    # Evaluate mode
    if args.evaluate:
        if not args.words:
            print("Error: Please specify a word to evaluate (e.g., --evaluate apple)")
            sys.exit(1)
        word = args.words.split(",")[0].strip().lower()
        evaluate_models(word)
        return

    # Parse specific words if provided
    if args.words:
        words = [w.strip().lower() for w in args.words.split(",")]
        # Validate words exist in our list
        invalid = [w for w in words if w not in all_words]
        if invalid:
            print(f"Warning: Unknown words (not in CHARACTER_DATA): {invalid}")
    else:
        words = all_words

    print(f"Generating {'high-contrast' if args.high_contrast else 'regular'} images")
    print(f"Model: {args.model}")
    print(f"Output directory: {PENDING_REVIEW_DIR}")
    print(f"Words to process: {len(words)}")
    print("-" * 50)

    results = {"success": [], "failed": [], "skipped": []}

    for i, word in enumerate(words):
        print(f"\n[{i + 1}/{len(words)}] {word}")

        result = generate_word_image(word, high_contrast=args.high_contrast, force=args.force, model=args.model)

        if result:
            if "pending_review" in result:
                results["success"].append(word)
            else:
                results["skipped"].append(word)
        else:
            results["failed"].append(word)

        # Delay between generations to avoid overwhelming ComfyUI
        if i < len(words) - 1:
            time.sleep(args.delay)

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Generated: {len(results['success'])}")
    print(f"Skipped (already exists): {len(results['skipped'])}")
    print(f"Failed: {len(results['failed'])}")

    if results["failed"]:
        print(f"\nFailed words: {', '.join(results['failed'])}")

    print(f"\nReview pending images at: {PENDING_REVIEW_DIR}")
    print("After approval, move images to:")
    print(f"  Regular: {APPROVED_REGULAR_DIR}")
    print(f"  High-contrast: {APPROVED_HC_DIR}")


if __name__ == "__main__":
    main()
