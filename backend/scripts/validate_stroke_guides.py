#!/usr/bin/env python3
"""
Stroke Guide Validation Script

Validates that step-by-step stroke guides match the actual font skeleton.
Compares skeleton-extracted paths vs JSON stroke definitions for all
character/font combinations.

Usage:
    python validate_stroke_guides.py --font fredoka
    python validate_stroke_guides.py --all
    python validate_stroke_guides.py --character P --font fredoka --visual
"""

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.font_strokes import (
    FONT_METADATA,
    get_character_strokes,
    load_strokes,
)
from app.services.stroke_path_generator import (
    calculate_path_distance,
    extract_high_resolution_paths,
    match_skeleton_to_metadata,
)
from app.services.trace_generator import get_available_fonts


@dataclass
class StrokeValidationResult:
    """Result of validating a single stroke."""
    stroke_index: int
    direction: str
    json_point_count: int
    skeleton_point_count: int
    matched: bool
    endpoint_distance_start: float
    endpoint_distance_end: float
    path_deviation: float
    curvature: str


@dataclass
class CharacterValidationResult:
    """Result of validating all strokes for a character."""
    character: str
    font: str
    json_stroke_count: int
    skeleton_stroke_count: int
    matched_strokes: int
    unmatched_strokes: int
    stroke_results: List[StrokeValidationResult]
    avg_path_deviation: float
    max_path_deviation: float
    overall_quality: str  # "excellent", "good", "fair", "poor"


def calculate_endpoint_distance(
    p1: List[float], p2: List[float]
) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def validate_character(
    character: str,
    font_name: Optional[str] = None,
    size: int = 400
) -> Optional[CharacterValidationResult]:
    """
    Validate stroke guides for a single character.

    Args:
        character: The character to validate
        font_name: Font name (None for default)
        size: Canvas size for extraction

    Returns:
        CharacterValidationResult or None if character not found
    """
    # Get JSON stroke data
    json_data = get_character_strokes(character, font_name)
    if json_data is None:
        return None

    json_strokes = json_data.get("strokes", [])
    if not json_strokes:
        return None

    # Extract skeleton paths
    skeleton_paths = extract_high_resolution_paths(character, size, font_name)

    # Match skeleton to JSON
    scale = size / 100.0
    matched_strokes = match_skeleton_to_metadata(
        skeleton_paths, json_strokes, size
    )

    # Analyze each stroke
    stroke_results = []
    total_deviation = 0
    max_deviation = 0
    matched_count = 0

    for i, (json_stroke, matched_stroke) in enumerate(zip(json_strokes, matched_strokes)):
        json_points = json_stroke["points"]
        matched_points = matched_stroke["points"]

        # Calculate endpoint distances
        json_start = [json_points[0][0] * scale, json_points[0][1] * scale]
        json_end = [json_points[-1][0] * scale, json_points[-1][1] * scale]
        matched_start = [matched_points[0][0] * scale, matched_points[0][1] * scale]
        matched_end = [matched_points[-1][0] * scale, matched_points[-1][1] * scale]

        start_dist = calculate_endpoint_distance(json_start, matched_start)
        end_dist = calculate_endpoint_distance(json_end, matched_end)

        # Calculate path deviation
        path_deviation = calculate_path_distance(
            [(p[0] * scale, p[1] * scale) for p in matched_points],
            [[p[0] * scale, p[1] * scale] for p in json_points]
        )

        total_deviation += path_deviation
        max_deviation = max(max_deviation, path_deviation)

        is_matched = matched_stroke.get("matched", False)
        if is_matched:
            matched_count += 1

        # Classify curvature
        curvature = matched_stroke.get("curvature", "unknown")

        stroke_results.append(StrokeValidationResult(
            stroke_index=i,
            direction=json_stroke.get("direction", "unknown"),
            json_point_count=len(json_points),
            skeleton_point_count=len(matched_points),
            matched=is_matched,
            endpoint_distance_start=start_dist,
            endpoint_distance_end=end_dist,
            path_deviation=path_deviation,
            curvature=curvature
        ))

    # Calculate overall quality
    avg_deviation = total_deviation / len(stroke_results) if stroke_results else 0

    if avg_deviation < 5 and matched_count == len(json_strokes):
        quality = "excellent"
    elif avg_deviation < 15 and matched_count >= len(json_strokes) * 0.8:
        quality = "good"
    elif avg_deviation < 30 and matched_count >= len(json_strokes) * 0.5:
        quality = "fair"
    else:
        quality = "poor"

    return CharacterValidationResult(
        character=character,
        font=font_name or "default",
        json_stroke_count=len(json_strokes),
        skeleton_stroke_count=len(skeleton_paths),
        matched_strokes=matched_count,
        unmatched_strokes=len(json_strokes) - matched_count,
        stroke_results=stroke_results,
        avg_path_deviation=avg_deviation,
        max_path_deviation=max_deviation,
        overall_quality=quality
    )


def validate_font(font_name: Optional[str] = None) -> Dict[str, CharacterValidationResult]:
    """
    Validate all characters for a specific font.

    Returns:
        Dictionary mapping character to validation result
    """
    # Get all characters from font
    font_key = font_name or "fredoka"
    font_data = load_strokes(font_key.lower().replace("-regular", ""))

    if not font_data:
        print(f"Error: Could not load font data for {font_name}")
        return {}

    characters = font_data.get("characters", {})
    results = {}

    for char in characters:
        result = validate_character(char, font_name)
        if result:
            results[char] = result

    return results


def generate_visual_comparison(
    character: str,
    font_name: Optional[str] = None,
    output_path: Optional[str] = None,
    size: int = 400
) -> None:
    """
    Generate a visual comparison image showing JSON strokes vs skeleton paths.
    Requires PIL/Pillow.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Warning: PIL/Pillow not available for visual comparison")
        return

    # Get data
    json_data = get_character_strokes(character, font_name)
    if not json_data:
        print(f"Character {character} not found")
        return

    json_strokes = json_data.get("strokes", [])
    skeleton_paths = extract_high_resolution_paths(character, size, font_name)
    matched_strokes = match_skeleton_to_metadata(skeleton_paths, json_strokes, size)

    scale = size / 100.0

    # Create comparison image (side by side)
    img = Image.new("RGB", (size * 2 + 20, size), "white")
    draw = ImageDraw.Draw(img)

    # Colors
    json_colors = ["#FF0000", "#00AA00", "#0000FF", "#FF8800", "#AA00AA"]
    skel_colors = ["#FF6666", "#66CC66", "#6666FF", "#FFAA66", "#CC66CC"]

    # Draw JSON strokes on left
    draw.text((10, 10), f"JSON ({len(json_strokes)} strokes)", fill="black")
    for i, stroke in enumerate(json_strokes):
        points = [(p[0] * scale, p[1] * scale) for p in stroke["points"]]
        if len(points) >= 2:
            color = json_colors[i % len(json_colors)]
            draw.line(points, fill=color, width=3)
            # Mark start
            draw.ellipse([points[0][0]-5, points[0][1]-5, points[0][0]+5, points[0][1]+5],
                        fill="green")
            # Mark end
            draw.ellipse([points[-1][0]-5, points[-1][1]-5, points[-1][0]+5, points[-1][1]+5],
                        fill="red")

    # Draw skeleton paths on right
    offset_x = size + 20
    draw.text((offset_x + 10, 10), f"Skeleton ({len(matched_strokes)} matched)", fill="black")
    for i, stroke in enumerate(matched_strokes):
        points = [(p[0] * scale + offset_x, p[1] * scale) for p in stroke["points"]]
        if len(points) >= 2:
            color = skel_colors[i % len(skel_colors)]
            draw.line(points, fill=color, width=3)
            # Mark start
            draw.ellipse([points[0][0]-5, points[0][1]-5, points[0][0]+5, points[0][1]+5],
                        fill="green")
            # Mark end
            draw.ellipse([points[-1][0]-5, points[-1][1]-5, points[-1][0]+5, points[-1][1]+5],
                        fill="red")

    # Draw center divider
    draw.line([(size + 10, 0), (size + 10, size)], fill="gray", width=2)

    # Save or show
    if output_path:
        img.save(output_path)
        print(f"Saved visual comparison to {output_path}")
    else:
        img.show()


def print_validation_report(
    results: Dict[str, CharacterValidationResult],
    verbose: bool = False
) -> None:
    """Print a formatted validation report."""
    if not results:
        print("No results to report")
        return

    # Summary statistics
    total = len(results)
    excellent = sum(1 for r in results.values() if r.overall_quality == "excellent")
    good = sum(1 for r in results.values() if r.overall_quality == "good")
    fair = sum(1 for r in results.values() if r.overall_quality == "fair")
    poor = sum(1 for r in results.values() if r.overall_quality == "poor")

    print("\n" + "=" * 60)
    print("STROKE GUIDE VALIDATION REPORT")
    print("=" * 60)

    first_result = list(results.values())[0]
    print(f"Font: {first_result.font}")
    print(f"Characters validated: {total}")
    print()

    print("Quality Summary:")
    print(f"  Excellent: {excellent} ({excellent*100/total:.1f}%)")
    print(f"  Good:      {good} ({good*100/total:.1f}%)")
    print(f"  Fair:      {fair} ({fair*100/total:.1f}%)")
    print(f"  Poor:      {poor} ({poor*100/total:.1f}%)")
    print()

    # List problematic characters
    if poor > 0 or fair > 0:
        print("Characters needing attention:")
        for char, result in sorted(results.items()):
            if result.overall_quality in ["poor", "fair"]:
                print(f"  '{char}': {result.overall_quality} "
                      f"(avg deviation: {result.avg_path_deviation:.1f}, "
                      f"matched: {result.matched_strokes}/{result.json_stroke_count})")

    # Detailed results if verbose
    if verbose:
        print("\n" + "-" * 60)
        print("DETAILED RESULTS")
        print("-" * 60)

        for char, result in sorted(results.items()):
            print(f"\nCharacter: '{char}'")
            print(f"  Quality: {result.overall_quality}")
            print(f"  JSON strokes: {result.json_stroke_count}")
            print(f"  Skeleton strokes: {result.skeleton_stroke_count}")
            print(f"  Matched: {result.matched_strokes}")
            print(f"  Avg deviation: {result.avg_path_deviation:.2f}")
            print(f"  Max deviation: {result.max_path_deviation:.2f}")

            for sr in result.stroke_results:
                status = "✓" if sr.matched else "✗"
                print(f"    Stroke {sr.stroke_index + 1}: {status} "
                      f"dir={sr.direction}, "
                      f"pts={sr.json_point_count}->{sr.skeleton_point_count}, "
                      f"dev={sr.path_deviation:.1f}")

    print("\n" + "=" * 60)


def export_report_json(
    results: Dict[str, CharacterValidationResult],
    output_path: str
) -> None:
    """Export validation results as JSON."""
    report = {
        "font": list(results.values())[0].font if results else "unknown",
        "total_characters": len(results),
        "summary": {
            "excellent": sum(1 for r in results.values() if r.overall_quality == "excellent"),
            "good": sum(1 for r in results.values() if r.overall_quality == "good"),
            "fair": sum(1 for r in results.values() if r.overall_quality == "fair"),
            "poor": sum(1 for r in results.values() if r.overall_quality == "poor"),
        },
        "characters": {}
    }

    for char, result in results.items():
        report["characters"][char] = {
            "quality": result.overall_quality,
            "json_strokes": result.json_stroke_count,
            "skeleton_strokes": result.skeleton_stroke_count,
            "matched": result.matched_strokes,
            "avg_deviation": round(result.avg_path_deviation, 2),
            "max_deviation": round(result.max_path_deviation, 2),
            "strokes": [
                {
                    "index": sr.stroke_index,
                    "direction": sr.direction,
                    "matched": sr.matched,
                    "deviation": round(sr.path_deviation, 2),
                    "curvature": sr.curvature
                }
                for sr in result.stroke_results
            ]
        }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Exported report to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate stroke guides against font skeletons"
    )
    parser.add_argument(
        "--font",
        type=str,
        help="Font to validate (e.g., fredoka, nunito)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all available fonts"
    )
    parser.add_argument(
        "--character",
        type=str,
        help="Validate a specific character"
    )
    parser.add_argument(
        "--visual",
        action="store_true",
        help="Generate visual comparison images"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed results"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for reports and images"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Export results as JSON"
    )

    args = parser.parse_args()

    # Create output directory if specified
    if args.output:
        os.makedirs(args.output, exist_ok=True)

    # Validate specific character
    if args.character:
        result = validate_character(args.character, args.font)
        if result:
            print_validation_report({args.character: result}, verbose=True)
            if args.visual:
                output_path = None
                if args.output:
                    output_path = os.path.join(
                        args.output,
                        f"{args.character}_{args.font or 'default'}_comparison.png"
                    )
                generate_visual_comparison(args.character, args.font, output_path)
        else:
            print(f"Character '{args.character}' not found")
        return

    # Validate all fonts
    if args.all:
        for font_key in FONT_METADATA:
            print(f"\nValidating font: {font_key}")
            results = validate_font(font_key)
            print_validation_report(results, verbose=args.verbose)

            if args.json and args.output:
                json_path = os.path.join(args.output, f"{font_key}_validation.json")
                export_report_json(results, json_path)
        return

    # Validate single font
    font = args.font or "fredoka"
    print(f"Validating font: {font}")
    results = validate_font(font)
    print_validation_report(results, verbose=args.verbose)

    if args.json and args.output:
        json_path = os.path.join(args.output, f"{font}_validation.json")
        export_report_json(results, json_path)

    # Generate visual comparisons for poor/fair quality
    if args.visual and args.output:
        for char, result in results.items():
            if result.overall_quality in ["poor", "fair"]:
                output_path = os.path.join(
                    args.output,
                    f"{char}_{font}_comparison.png"
                )
                generate_visual_comparison(char, font, output_path)


if __name__ == "__main__":
    main()
