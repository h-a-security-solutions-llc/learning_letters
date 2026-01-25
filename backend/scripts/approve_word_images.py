#!/usr/bin/env python3
"""
Approve and process word images from pending review.

This script helps manage word images:
- List pending images
- Approve images (move to static/words directory)
- Remove background and convert to SVG
- Reject/delete images

Usage:
    # List pending images
    python scripts/approve_word_images.py --list

    # Approve specific images
    python scripts/approve_word_images.py apple_regular.png ball_regular.png

    # Approve all pending images
    python scripts/approve_word_images.py --all

    # Reject/delete specific images
    python scripts/approve_word_images.py --reject apple_regular.png

    # Skip background removal (keep original PNG)
    python scripts/approve_word_images.py --no-rembg apple_regular.png
"""

import argparse
import subprocess  # nosec B404 - Used for vtracer with controlled inputs
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Directories
SCRIPT_DIR = Path(__file__).parent
PENDING_REVIEW_DIR = SCRIPT_DIR / "pending_review"
APPROVED_REGULAR_DIR = SCRIPT_DIR.parent / "app" / "static" / "words" / "regular"
APPROVED_HC_DIR = SCRIPT_DIR.parent / "app" / "static" / "words" / "high-contrast"


def remove_background(input_path: Path, output_path: Path) -> bool:
    """Remove background from image using rembg."""
    try:
        from rembg import remove

        with open(input_path, "rb") as inp:
            input_data = inp.read()

        output_data = remove(input_data)

        with open(output_path, "wb") as out:
            out.write(output_data)

        return True
    except Exception as e:
        print(f"  Background removal failed: {e}")
        return False


def convert_to_svg(png_path: Path, svg_path: Path) -> bool:
    """Convert PNG to SVG using vtracer."""
    try:
        # nosec B603, B607 - Paths are controlled
        result = subprocess.run(  # nosec
            [
                "vtracer",
                "--input",
                str(png_path),
                "--output",
                str(svg_path),
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
        print(f"  SVG conversion failed: {e}")
        return False


def get_pending_images() -> list[Path]:
    """Get list of pending images."""
    if not PENDING_REVIEW_DIR.exists():
        return []
    return sorted(PENDING_REVIEW_DIR.glob("*.png"))


def parse_image_name(filename: str) -> tuple[str, bool]:
    """Parse image filename to get word and variant."""
    # Format: word_variant.png (e.g., apple_regular.png, apple_hc.png)
    name = filename.replace(".png", "")
    if name.endswith("_hc"):
        return name[:-3], True
    elif name.endswith("_regular"):
        return name[:-8], False
    else:
        # Assume regular if no suffix
        return name, False


def approve_image(image_path: Path, use_rembg: bool = True, convert_svg: bool = True) -> bool:
    """Approve an image: remove background, convert to SVG, move to approved dir."""
    filename = image_path.name
    word, is_hc = parse_image_name(filename)

    output_dir = APPROVED_HC_DIR if is_hc else APPROVED_REGULAR_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nProcessing: {filename}")
    print(f"  Word: {word}, Variant: {'high-contrast' if is_hc else 'regular'}")

    # Step 1: Remove background (if enabled)
    if use_rembg:
        print("  Removing background...")
        temp_path = output_dir / f"{word}_temp.png"
        if not remove_background(image_path, temp_path):
            print("  Falling back to original image (no background removal)")
            temp_path = image_path
    else:
        temp_path = image_path

    # Step 2: Convert to SVG (if enabled and rembg succeeded)
    final_path = output_dir / f"{word}.png"
    svg_path = output_dir / f"{word}.svg"

    if convert_svg and use_rembg:
        print("  Converting to SVG...")
        # First copy the transparent PNG
        if temp_path != image_path:
            import shutil

            shutil.copy2(temp_path, final_path)

        if convert_to_svg(final_path, svg_path):
            print(f"  Created: {svg_path.name}")
            # Keep both PNG and SVG
        else:
            print("  SVG conversion failed, keeping PNG")
    else:
        # Just copy the image
        import shutil

        shutil.copy2(temp_path, final_path)
        print(f"  Saved: {final_path.name}")

    # Clean up temp file
    if use_rembg and temp_path.exists() and temp_path != image_path:
        temp_path.unlink()

    # Remove from pending
    image_path.unlink()
    print("  Approved!")

    return True


def reject_image(image_path: Path) -> bool:
    """Reject/delete an image from pending review."""
    try:
        image_path.unlink()
        print(f"Rejected: {image_path.name}")
        return True
    except Exception as e:
        print(f"Error rejecting {image_path.name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Approve and process word images from pending review")
    parser.add_argument(
        "images",
        nargs="*",
        help="Image filenames to approve (e.g., apple_regular.png)",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List pending images",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Approve all pending images",
    )
    parser.add_argument(
        "--reject",
        "-r",
        action="store_true",
        help="Reject/delete specified images",
    )
    parser.add_argument(
        "--no-rembg",
        action="store_true",
        help="Skip background removal",
    )
    parser.add_argument(
        "--no-svg",
        action="store_true",
        help="Skip SVG conversion",
    )

    args = parser.parse_args()

    pending = get_pending_images()

    if args.list or (not args.images and not args.all):
        if not pending:
            print("No pending images.")
            print("\nGenerate images with: python scripts/generate_word_images.py")
        else:
            print(f"Pending images ({len(pending)}):\n")
            for img in pending:
                word, is_hc = parse_image_name(img.name)
                variant = "high-contrast" if is_hc else "regular"
                print(f"  {img.name:30} ({word}, {variant})")
            print("\nTo approve: python scripts/approve_word_images.py <filename>")
            print("To approve all: python scripts/approve_word_images.py --all")
        return

    # Get images to process
    if args.all:
        images_to_process = pending
    else:
        images_to_process = []
        for name in args.images:
            path = PENDING_REVIEW_DIR / name
            if path.exists():
                images_to_process.append(path)
            else:
                print(f"Warning: {name} not found in pending review")

    if not images_to_process:
        print("No images to process.")
        return

    # Process images
    if args.reject:
        for img in images_to_process:
            reject_image(img)
    else:
        for img in images_to_process:
            approve_image(
                img,
                use_rembg=not args.no_rembg,
                convert_svg=not args.no_svg,
            )

    # Show remaining pending
    remaining = get_pending_images()
    if remaining:
        print(f"\n{len(remaining)} images still pending review.")


if __name__ == "__main__":
    main()
