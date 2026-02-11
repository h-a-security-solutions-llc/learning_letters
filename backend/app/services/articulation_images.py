"""
Articulation image generation service using ComfyUI.
Generates mouth position and hand gesture images for teaching letter sounds.

NOTE: AI-generated images may not be anatomically accurate enough for
educational purposes. These should be reviewed and potentially replaced
with professionally created illustrations.
"""

import os
import shutil
import time
from typing import Optional

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from app.services.articulation_cues import LETTER_TO_SOUND, SOUND_CUES

# Load environment variables
load_dotenv()

# Directory for articulation images
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "articulation")
MOUTH_DIR = os.path.join(IMAGES_DIR, "mouth")
HAND_DIR = os.path.join(IMAGES_DIR, "hand")
SIDE_VIEW_DIR = os.path.join(IMAGES_DIR, "side-view")

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

# Model to use
CHECKPOINT_MODEL = "hassakuXLIllustrious_v33.safetensors"

# Prompt templates for articulation images
# These aim for clear, educational-style illustrations

MOUTH_FRONT_PROMPT = """
simple educational diagram of human mouth and lips from front view,
{mouth_description},
medical illustration style, clean lines, labeled anatomy,
white background, clear detail, educational chart,
showing lip position and mouth opening,
simple flat colors, vector style, kid-friendly
"""

MOUTH_SIDE_PROMPT = """
simple educational cross-section diagram of human mouth from side view,
showing tongue position: {tongue_description},
medical illustration style, clean lines, anatomy diagram,
white background, clear detail, educational chart,
showing tongue, teeth, palate, throat,
simple flat colors, vector style
"""

HAND_CUE_PROMPT = """
simple illustration of hand gesture for teaching phonics,
{hand_description},
kid-friendly cartoon style, clear gesture,
white background, simple, educational,
clean lines, bright colors
"""

NEGATIVE_PROMPT = (
    "realistic photo, photorealistic, complex background, "
    "blurry, low quality, text, words, watermark, "
    "scary, ugly, distorted, multiple hands"
)


def check_comfyui_available() -> bool:
    """Check if ComfyUI is running and accessible."""
    try:
        response = requests.get(f"{COMFYUI_URL}/system_stats", timeout=5, auth=get_comfyui_auth())
        return response.status_code == 200
    except requests.RequestException:
        return False


def create_workflow(prompt: str, negative_prompt: str, filename: str) -> dict:
    """Create a ComfyUI workflow for image generation."""
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
                "steps": 30,  # More steps for better quality
            },
        },
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename, "images": ["6", 0]}},
    }


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


def generate_mouth_image(sound_key: str, force: bool = False) -> Optional[str]:  # pragma: no cover
    """Generate a front-view mouth position image for a sound."""
    sound_data = SOUND_CUES.get(sound_key)
    if not sound_data:
        print(f"No sound data for '{sound_key}'")
        return None

    os.makedirs(MOUTH_DIR, exist_ok=True)
    output_path = os.path.join(MOUTH_DIR, f"{sound_key}.png")

    if not force and os.path.exists(output_path):
        print(f"Image already exists for '{sound_key}'")
        return output_path

    if not check_comfyui_available():
        print("ComfyUI is not available")
        return None

    # Build prompt from mouth description
    mouth_desc = sound_data.get("visual_description", sound_data.get("mouth_position", ""))
    prompt = MOUTH_FRONT_PROMPT.format(mouth_description=mouth_desc)

    workflow = create_workflow(prompt, NEGATIVE_PROMPT, f"mouth_{sound_key}")

    prompt_id = queue_prompt(workflow)
    if not prompt_id:
        print(f"Failed to queue prompt for '{sound_key}'")
        return None

    print(f"Generating mouth image for '{sound_key}' (prompt_id: {prompt_id})...")
    if not wait_for_completion(prompt_id):
        print(f"Timeout waiting for '{sound_key}'")
        return None

    # Find generated file
    generated_files = [
        f for f in os.listdir(COMFYUI_OUTPUT_DIR) if f.startswith(f"mouth_{sound_key}") and f.endswith(".png")
    ]

    if not generated_files:
        print(f"No output file found for '{sound_key}'")
        return None

    source_path = os.path.join(COMFYUI_OUTPUT_DIR, sorted(generated_files)[-1])
    shutil.copy2(source_path, output_path)
    print(f"Created mouth image for '{sound_key}'")
    return output_path


def generate_hand_cue_image(sound_key: str, force: bool = False) -> Optional[str]:  # pragma: no cover
    """Generate a hand gesture image for a sound."""
    sound_data = SOUND_CUES.get(sound_key)
    if not sound_data:
        print(f"No sound data for '{sound_key}'")
        return None

    os.makedirs(HAND_DIR, exist_ok=True)
    output_path = os.path.join(HAND_DIR, f"{sound_key}.png")

    if not force and os.path.exists(output_path):
        print(f"Hand cue image already exists for '{sound_key}'")
        return output_path

    if not check_comfyui_available():
        print("ComfyUI is not available")
        return None

    hand_desc = sound_data.get("hand_cue", "")
    if not hand_desc:
        print(f"No hand cue description for '{sound_key}'")
        return None

    prompt = HAND_CUE_PROMPT.format(hand_description=hand_desc)
    workflow = create_workflow(prompt, NEGATIVE_PROMPT, f"hand_{sound_key}")

    prompt_id = queue_prompt(workflow)
    if not prompt_id:
        print(f"Failed to queue prompt for '{sound_key}'")
        return None

    print(f"Generating hand cue image for '{sound_key}' (prompt_id: {prompt_id})...")
    if not wait_for_completion(prompt_id):
        print(f"Timeout waiting for '{sound_key}'")
        return None

    generated_files = [
        f for f in os.listdir(COMFYUI_OUTPUT_DIR) if f.startswith(f"hand_{sound_key}") and f.endswith(".png")
    ]

    if not generated_files:
        print(f"No output file found for '{sound_key}'")
        return None

    source_path = os.path.join(COMFYUI_OUTPUT_DIR, sorted(generated_files)[-1])
    shutil.copy2(source_path, output_path)
    print(f"Created hand cue image for '{sound_key}'")
    return output_path


def generate_all_articulation_images(force: bool = False) -> dict:  # pragma: no cover
    """Generate all articulation images."""
    results = {"mouth_success": [], "mouth_failed": [], "hand_success": [], "hand_failed": []}

    # Get unique sounds
    unique_sounds = set(LETTER_TO_SOUND.values())

    for i, sound_key in enumerate(sorted(unique_sounds)):
        print(f"\n[{i+1}/{len(unique_sounds)}] Processing '{sound_key}'...")

        # Generate mouth image
        if generate_mouth_image(sound_key, force):
            results["mouth_success"].append(sound_key)
        else:
            results["mouth_failed"].append(sound_key)

        time.sleep(1)  # Delay between generations

        # Generate hand cue image
        if generate_hand_cue_image(sound_key, force):
            results["hand_success"].append(sound_key)
        else:
            results["hand_failed"].append(sound_key)

        time.sleep(1)

    return results


def get_mouth_image_url(character: str) -> Optional[str]:
    """Get URL path to mouth position image for a character."""
    sound_key = LETTER_TO_SOUND.get(character)
    if not sound_key:
        return None

    png_path = os.path.join(MOUTH_DIR, f"{sound_key}.png")
    if os.path.exists(png_path):
        return f"/static/articulation/mouth/{sound_key}.png"
    return None


def get_hand_cue_image_url(character: str) -> Optional[str]:
    """Get URL path to hand cue image for a character."""
    sound_key = LETTER_TO_SOUND.get(character)
    if not sound_key:
        return None

    png_path = os.path.join(HAND_DIR, f"{sound_key}.png")
    if os.path.exists(png_path):
        return f"/static/articulation/hand/{sound_key}.png"
    return None


def get_articulation_image_stats() -> dict:
    """Get statistics about available articulation images."""
    unique_sounds = set(LETTER_TO_SOUND.values())

    mouth_available = []
    hand_available = []
    mouth_missing = []
    hand_missing = []

    for sound_key in unique_sounds:
        mouth_path = os.path.join(MOUTH_DIR, f"{sound_key}.png")
        hand_path = os.path.join(HAND_DIR, f"{sound_key}.png")

        if os.path.exists(mouth_path):
            mouth_available.append(sound_key)
        else:
            mouth_missing.append(sound_key)

        if os.path.exists(hand_path):
            hand_available.append(sound_key)
        else:
            hand_missing.append(sound_key)

    return {
        "total_sounds": len(unique_sounds),
        "mouth_available": len(mouth_available),
        "mouth_missing": len(mouth_missing),
        "hand_available": len(hand_available),
        "hand_missing": len(hand_missing),
        "mouth_missing_list": sorted(mouth_missing),
        "hand_missing_list": sorted(hand_missing),
    }


# CLI for running generation
if __name__ == "__main__":  # pragma: no cover
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.services.articulation_images <command>")
        print("Commands:")
        print("  stats         - Show image availability statistics")
        print("  generate      - Generate all missing images")
        print("  test <sound>  - Generate test image for one sound (e.g., 'test p')")
        sys.exit(1)

    command = sys.argv[1]

    if command == "stats":
        stats = get_articulation_image_stats()
        print(f"Total sounds: {stats['total_sounds']}")
        print(f"Mouth images available: {stats['mouth_available']}")
        print(f"Mouth images missing: {stats['mouth_missing']}")
        print(f"Hand images available: {stats['hand_available']}")
        print(f"Hand images missing: {stats['hand_missing']}")
        if stats["mouth_missing_list"]:
            print(f"\nMissing mouth images: {', '.join(stats['mouth_missing_list'])}")

    elif command == "generate":
        if not check_comfyui_available():
            print("Error: ComfyUI is not running or not accessible")
            print(f"Expected at: {COMFYUI_URL}")
            sys.exit(1)
        results = generate_all_articulation_images()
        print(f"\nMouth images: {len(results['mouth_success'])} success, {len(results['mouth_failed'])} failed")
        print(f"Hand images: {len(results['hand_success'])} success, {len(results['hand_failed'])} failed")

    elif command == "test" and len(sys.argv) > 2:
        sound_key = sys.argv[2]
        if sound_key not in SOUND_CUES:
            print(f"Unknown sound: {sound_key}")
            print(f"Available sounds: {', '.join(sorted(SOUND_CUES.keys()))}")
            sys.exit(1)

        if not check_comfyui_available():
            print("Error: ComfyUI is not running or not accessible")
            sys.exit(1)

        print(f"Testing generation for '{sound_key}'...")
        print(f"\nSound data:")
        for key, value in SOUND_CUES[sound_key].items():
            print(f"  {key}: {value}")

        print("\nGenerating mouth image...")
        mouth_path = generate_mouth_image(sound_key, force=True)
        print(f"Result: {mouth_path}")

        print("\nGenerating hand cue image...")
        hand_path = generate_hand_cue_image(sound_key, force=True)
        print(f"Result: {hand_path}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
