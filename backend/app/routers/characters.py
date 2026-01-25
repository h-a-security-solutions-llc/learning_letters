"""Characters router for character data, strokes, and guided drawing."""

import math
import os
from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.font_strokes import get_character_strokes, get_font_metadata

router = APIRouter()

# Stroke colors for visual distinction
STROKE_COLORS = [
    "#FF6B6B",  # Red
    "#4ECDC4",  # Teal
    "#FFE66D",  # Yellow
    "#95E1D3",  # Mint
    "#F38181",  # Coral
    "#AA96DA",  # Purple
]

# Direction to kid-friendly instruction mapping
DIRECTION_INSTRUCTIONS = {
    "down": "Start at the top. Draw straight down.",
    "up": "Start at the bottom. Draw straight up.",
    "right": "Start on the left. Draw to the right.",
    "left": "Start on the right. Draw to the left.",
    "down-left": "Start at the top. Draw down to the left.",
    "down-right": "Start at the top. Draw down to the right.",
    "up-left": "Start at the bottom. Draw up to the left.",
    "up-right": "Start at the bottom. Draw up to the right.",
    "curve-left": "Start on the right. Curve around to the left.",
    "curve-right": "Start on the left. Curve around to the right.",
    "right-curve": "Draw to the right, then curve down.",
    "down-curve": "Draw down, then curve at the bottom.",
    "curve-down": "Start with a curve, then go down.",
    "down-curve-up": "Draw down, curve at the bottom, then back up.",
    "oval": "Draw a round circle shape.",
    "s-curve": "Make an S shape, curving back and forth.",
    "curve-in": "Curve around, then come back in.",
    "curve-loop": "Curve around in a loop shape.",
    "curve": "Follow the curving path.",
    "slant-down": "Draw at an angle going down.",
    "figure-8": "Draw a figure 8 shape.",
    "loop-down": "Make a loop, then go down.",
    "dot": "Make a small dot.",
    "curve-up": "Curve upward.",
}


class StrokeValidationRequest(BaseModel):
    """Request model for validating a drawn stroke."""

    stroke_index: int
    drawn_points: List[List[float]]
    font: Optional[str] = None
    tolerance_multiplier: Optional[float] = 1.0


# Character data with stroke paths for tracing
# Paths are SVG-like instructions normalized to 0-100 coordinate space
# Each stroke has points and arrows showing direction

CHARACTERS = {
    # Uppercase letters
    "A": {
        "type": "uppercase",
        "phonetic": "ay",
        "sound": "ah as in apple",
        "strokes": [
            {"points": [[50, 15], [20, 85]], "direction": "down-left"},
            {"points": [[50, 15], [80, 85]], "direction": "down-right"},
            {"points": [[32, 55], [68, 55]], "direction": "right"},
        ],
    },
    "B": {
        "type": "uppercase",
        "phonetic": "bee",
        "sound": "buh as in ball",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 10], [60, 10], [70, 25], [60, 50], [25, 50]], "direction": "right-curve"},
            {"points": [[25, 50], [65, 50], [75, 70], [65, 90], [25, 90]], "direction": "right-curve"},
        ],
    },
    "C": {
        "type": "uppercase",
        "phonetic": "see",
        "sound": "kuh as in cat",
        "strokes": [
            {"points": [[75, 20], [50, 10], [25, 30], [25, 70], [50, 90], [75, 80]], "direction": "curve-left"}
        ],
    },
    "D": {
        "type": "uppercase",
        "phonetic": "dee",
        "sound": "duh as in dog",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 10], [55, 10], [75, 30], [75, 70], [55, 90], [25, 90]], "direction": "curve-right"},
        ],
    },
    "E": {
        "type": "uppercase",
        "phonetic": "ee",
        "sound": "eh as in elephant",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 10], [75, 10]], "direction": "right"},
            {"points": [[25, 50], [65, 50]], "direction": "right"},
            {"points": [[25, 90], [75, 90]], "direction": "right"},
        ],
    },
    "F": {
        "type": "uppercase",
        "phonetic": "ef",
        "sound": "fuh as in fish",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 10], [75, 10]], "direction": "right"},
            {"points": [[25, 50], [60, 50]], "direction": "right"},
        ],
    },
    "G": {
        "type": "uppercase",
        "phonetic": "jee",
        "sound": "guh as in goat",
        "strokes": [
            {
                "points": [[75, 20], [50, 10], [25, 30], [25, 70], [50, 90], [75, 70], [75, 50], [55, 50]],
                "direction": "curve-in",
            }
        ],
    },
    "H": {
        "type": "uppercase",
        "phonetic": "aych",
        "sound": "huh as in hat",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[75, 10], [75, 90]], "direction": "down"},
            {"points": [[25, 50], [75, 50]], "direction": "right"},
        ],
    },
    "I": {
        "type": "uppercase",
        "phonetic": "eye",
        "sound": "ih as in igloo",
        "strokes": [
            {"points": [[35, 10], [65, 10]], "direction": "right"},
            {"points": [[50, 10], [50, 90]], "direction": "down"},
            {"points": [[35, 90], [65, 90]], "direction": "right"},
        ],
    },
    "J": {
        "type": "uppercase",
        "phonetic": "jay",
        "sound": "juh as in jump",
        "strokes": [
            {"points": [[35, 10], [65, 10]], "direction": "right"},
            {"points": [[55, 10], [55, 70], [45, 85], [30, 80]], "direction": "down-curve"},
        ],
    },
    "K": {
        "type": "uppercase",
        "phonetic": "kay",
        "sound": "kuh as in kite",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[70, 10], [25, 55]], "direction": "down-left"},
            {"points": [[40, 45], [70, 90]], "direction": "down-right"},
        ],
    },
    "L": {
        "type": "uppercase",
        "phonetic": "el",
        "sound": "luh as in lion",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 90], [75, 90]], "direction": "right"},
        ],
    },
    "M": {
        "type": "uppercase",
        "phonetic": "em",
        "sound": "muh as in moon",
        "strokes": [
            {"points": [[20, 90], [20, 10]], "direction": "up"},
            {"points": [[20, 10], [50, 50]], "direction": "down-right"},
            {"points": [[50, 50], [80, 10]], "direction": "up-right"},
            {"points": [[80, 10], [80, 90]], "direction": "down"},
        ],
    },
    "N": {
        "type": "uppercase",
        "phonetic": "en",
        "sound": "nuh as in nest",
        "strokes": [
            {"points": [[25, 90], [25, 10]], "direction": "up"},
            {"points": [[25, 10], [75, 90]], "direction": "down-right"},
            {"points": [[75, 90], [75, 10]], "direction": "up"},
        ],
    },
    "O": {
        "type": "uppercase",
        "phonetic": "oh",
        "sound": "ah as in octopus",
        "strokes": [
            {"points": [[50, 10], [25, 30], [25, 70], [50, 90], [75, 70], [75, 30], [50, 10]], "direction": "oval"}
        ],
    },
    "P": {
        "type": "uppercase",
        "phonetic": "pee",
        "sound": "puh as in pig",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 10], [60, 10], [75, 25], [75, 40], [60, 55], [25, 55]], "direction": "curve-right"},
        ],
    },
    "Q": {
        "type": "uppercase",
        "phonetic": "kyoo",
        "sound": "kwuh as in queen",
        "strokes": [
            {"points": [[50, 10], [25, 30], [25, 70], [50, 90], [75, 70], [75, 30], [50, 10]], "direction": "oval"},
            {"points": [[55, 70], [80, 95]], "direction": "down-right"},
        ],
    },
    "R": {
        "type": "uppercase",
        "phonetic": "ar",
        "sound": "ruh as in rabbit",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 10], [60, 10], [75, 25], [60, 50], [25, 50]], "direction": "curve-right"},
            {"points": [[50, 50], [75, 90]], "direction": "down-right"},
        ],
    },
    "S": {
        "type": "uppercase",
        "phonetic": "ess",
        "sound": "sss as in snake",
        "strokes": [
            {
                "points": [
                    [70, 20],
                    [50, 10],
                    [30, 20],
                    [25, 35],
                    [35, 50],
                    [65, 55],
                    [75, 70],
                    [65, 85],
                    [50, 90],
                    [30, 85],
                ],
                "direction": "s-curve",
            }
        ],
    },
    "T": {
        "type": "uppercase",
        "phonetic": "tee",
        "sound": "tuh as in tiger",
        "strokes": [
            {"points": [[20, 10], [80, 10]], "direction": "right"},
            {"points": [[50, 10], [50, 90]], "direction": "down"},
        ],
    },
    "U": {
        "type": "uppercase",
        "phonetic": "yoo",
        "sound": "uh as in umbrella",
        "strokes": [{"points": [[25, 10], [25, 70], [50, 90], [75, 70], [75, 10]], "direction": "down-curve-up"}],
    },
    "V": {
        "type": "uppercase",
        "phonetic": "vee",
        "sound": "vuh as in van",
        "strokes": [
            {"points": [[20, 10], [50, 90]], "direction": "down-right"},
            {"points": [[50, 90], [80, 10]], "direction": "up-right"},
        ],
    },
    "W": {
        "type": "uppercase",
        "phonetic": "double-yoo",
        "sound": "wuh as in water",
        "strokes": [
            {"points": [[15, 10], [30, 90]], "direction": "down-right"},
            {"points": [[30, 90], [50, 40]], "direction": "up-right"},
            {"points": [[50, 40], [70, 90]], "direction": "down-right"},
            {"points": [[70, 90], [85, 10]], "direction": "up-right"},
        ],
    },
    "X": {
        "type": "uppercase",
        "phonetic": "eks",
        "sound": "ks as in box",
        "strokes": [
            {"points": [[20, 10], [80, 90]], "direction": "down-right"},
            {"points": [[80, 10], [20, 90]], "direction": "down-left"},
        ],
    },
    "Y": {
        "type": "uppercase",
        "phonetic": "why",
        "sound": "yuh as in yellow",
        "strokes": [
            {"points": [[20, 10], [50, 50]], "direction": "down-right"},
            {"points": [[80, 10], [50, 50]], "direction": "down-left"},
            {"points": [[50, 50], [50, 90]], "direction": "down"},
        ],
    },
    "Z": {
        "type": "uppercase",
        "phonetic": "zee",
        "sound": "zzz as in zebra",
        "strokes": [
            {"points": [[20, 10], [80, 10]], "direction": "right"},
            {"points": [[80, 10], [20, 90]], "direction": "down-left"},
            {"points": [[20, 90], [80, 90]], "direction": "right"},
        ],
    },
    # Lowercase letters
    "a": {
        "type": "lowercase",
        "phonetic": "ay",
        "sound": "ah as in apple",
        "strokes": [
            {"points": [[65, 40], [45, 35], [30, 45], [30, 70], [45, 80], [65, 75]], "direction": "curve-left"},
            {"points": [[65, 35], [65, 80]], "direction": "down"},
        ],
    },
    "b": {
        "type": "lowercase",
        "phonetic": "bee",
        "sound": "buh as in ball",
        "strokes": [
            {"points": [[30, 10], [30, 80]], "direction": "down"},
            {"points": [[30, 50], [45, 40], [60, 50], [60, 70], [45, 80], [30, 70]], "direction": "curve-right"},
        ],
    },
    "c": {
        "type": "lowercase",
        "phonetic": "see",
        "sound": "kuh as in cat",
        "strokes": [
            {"points": [[65, 45], [50, 35], [35, 50], [35, 65], [50, 80], [65, 70]], "direction": "curve-left"}
        ],
    },
    "d": {
        "type": "lowercase",
        "phonetic": "dee",
        "sound": "duh as in dog",
        "strokes": [
            {"points": [[65, 50], [50, 40], [35, 50], [35, 70], [50, 80], [65, 70]], "direction": "curve-left"},
            {"points": [[65, 10], [65, 80]], "direction": "down"},
        ],
    },
    "e": {
        "type": "lowercase",
        "phonetic": "ee",
        "sound": "eh as in elephant",
        "strokes": [
            {"points": [[35, 55], [65, 55]], "direction": "right"},
            {"points": [[65, 55], [65, 45], [50, 35], [35, 50], [35, 65], [50, 80], [65, 75]], "direction": "curve"},
        ],
    },
    "f": {
        "type": "lowercase",
        "phonetic": "ef",
        "sound": "fuh as in fish",
        "strokes": [
            {"points": [[60, 20], [50, 10], [40, 20], [40, 80]], "direction": "curve-down"},
            {"points": [[25, 40], [55, 40]], "direction": "right"},
        ],
    },
    "g": {
        "type": "lowercase",
        "phonetic": "jee",
        "sound": "guh as in goat",
        "strokes": [
            {"points": [[65, 50], [50, 40], [35, 50], [35, 65], [50, 75], [65, 65]], "direction": "curve-left"},
            {"points": [[65, 40], [65, 90], [50, 100], [35, 95]], "direction": "down-curve"},
        ],
    },
    "h": {
        "type": "lowercase",
        "phonetic": "aych",
        "sound": "huh as in hat",
        "strokes": [
            {"points": [[30, 10], [30, 80]], "direction": "down"},
            {"points": [[30, 50], [45, 40], [60, 50], [60, 80]], "direction": "curve-down"},
        ],
    },
    "i": {
        "type": "lowercase",
        "phonetic": "eye",
        "sound": "ih as in igloo",
        "strokes": [
            {"points": [[50, 40], [50, 80]], "direction": "down"},
            {"points": [[50, 25], [50, 28]], "direction": "dot"},
        ],
    },
    "j": {
        "type": "lowercase",
        "phonetic": "jay",
        "sound": "juh as in jump",
        "strokes": [
            {"points": [[55, 40], [55, 90], [45, 100], [35, 95]], "direction": "down-curve"},
            {"points": [[55, 25], [55, 28]], "direction": "dot"},
        ],
    },
    "k": {
        "type": "lowercase",
        "phonetic": "kay",
        "sound": "kuh as in kite",
        "strokes": [
            {"points": [[30, 10], [30, 80]], "direction": "down"},
            {"points": [[60, 40], [30, 60]], "direction": "down-left"},
            {"points": [[40, 55], [60, 80]], "direction": "down-right"},
        ],
    },
    "l": {
        "type": "lowercase",
        "phonetic": "el",
        "sound": "luh as in lion",
        "strokes": [{"points": [[50, 10], [50, 80]], "direction": "down"}],
    },
    "m": {
        "type": "lowercase",
        "phonetic": "em",
        "sound": "muh as in moon",
        "strokes": [
            {"points": [[20, 40], [20, 80]], "direction": "down"},
            {"points": [[20, 50], [35, 40], [50, 50], [50, 80]], "direction": "curve-down"},
            {"points": [[50, 50], [65, 40], [80, 50], [80, 80]], "direction": "curve-down"},
        ],
    },
    "n": {
        "type": "lowercase",
        "phonetic": "en",
        "sound": "nuh as in nest",
        "strokes": [
            {"points": [[30, 40], [30, 80]], "direction": "down"},
            {"points": [[30, 50], [50, 40], [65, 50], [65, 80]], "direction": "curve-down"},
        ],
    },
    "o": {
        "type": "lowercase",
        "phonetic": "oh",
        "sound": "ah as in octopus",
        "strokes": [
            {"points": [[50, 35], [35, 50], [35, 65], [50, 80], [65, 65], [65, 50], [50, 35]], "direction": "oval"}
        ],
    },
    "p": {
        "type": "lowercase",
        "phonetic": "pee",
        "sound": "puh as in pig",
        "strokes": [
            {"points": [[30, 40], [30, 100]], "direction": "down"},
            {"points": [[30, 50], [45, 40], [60, 50], [60, 65], [45, 75], [30, 65]], "direction": "curve-right"},
        ],
    },
    "q": {
        "type": "lowercase",
        "phonetic": "kyoo",
        "sound": "kwuh as in queen",
        "strokes": [
            {"points": [[65, 50], [50, 40], [35, 50], [35, 65], [50, 75], [65, 65]], "direction": "curve-left"},
            {"points": [[65, 40], [65, 100]], "direction": "down"},
        ],
    },
    "r": {
        "type": "lowercase",
        "phonetic": "ar",
        "sound": "ruh as in rabbit",
        "strokes": [
            {"points": [[35, 40], [35, 80]], "direction": "down"},
            {"points": [[35, 55], [50, 42], [65, 45]], "direction": "curve-up"},
        ],
    },
    "s": {
        "type": "lowercase",
        "phonetic": "ess",
        "sound": "sss as in snake",
        "strokes": [
            {
                "points": [[60, 42], [50, 38], [38, 45], [40, 55], [60, 62], [62, 72], [50, 78], [38, 75]],
                "direction": "s-curve",
            }
        ],
    },
    "t": {
        "type": "lowercase",
        "phonetic": "tee",
        "sound": "tuh as in tiger",
        "strokes": [
            {"points": [[45, 15], [45, 75], [55, 80], [65, 78]], "direction": "down-curve"},
            {"points": [[30, 40], [60, 40]], "direction": "right"},
        ],
    },
    "u": {
        "type": "lowercase",
        "phonetic": "yoo",
        "sound": "uh as in umbrella",
        "strokes": [
            {"points": [[30, 40], [30, 65], [45, 78], [60, 70]], "direction": "down-curve"},
            {"points": [[60, 40], [60, 80]], "direction": "down"},
        ],
    },
    "v": {
        "type": "lowercase",
        "phonetic": "vee",
        "sound": "vuh as in van",
        "strokes": [
            {"points": [[30, 40], [50, 80]], "direction": "down-right"},
            {"points": [[50, 80], [70, 40]], "direction": "up-right"},
        ],
    },
    "w": {
        "type": "lowercase",
        "phonetic": "double-yoo",
        "sound": "wuh as in water",
        "strokes": [
            {"points": [[20, 40], [30, 80]], "direction": "down-right"},
            {"points": [[30, 80], [45, 55]], "direction": "up-right"},
            {"points": [[45, 55], [60, 80]], "direction": "down-right"},
            {"points": [[60, 80], [75, 40]], "direction": "up-right"},
        ],
    },
    "x": {
        "type": "lowercase",
        "phonetic": "eks",
        "sound": "ks as in box",
        "strokes": [
            {"points": [[30, 40], [70, 80]], "direction": "down-right"},
            {"points": [[70, 40], [30, 80]], "direction": "down-left"},
        ],
    },
    "y": {
        "type": "lowercase",
        "phonetic": "why",
        "sound": "yuh as in yellow",
        "strokes": [
            {"points": [[30, 40], [50, 70]], "direction": "down-right"},
            {"points": [[70, 40], [50, 70], [40, 90], [30, 95]], "direction": "down-curve"},
        ],
    },
    "z": {
        "type": "lowercase",
        "phonetic": "zee",
        "sound": "zzz as in zebra",
        "strokes": [
            {"points": [[30, 40], [70, 40]], "direction": "right"},
            {"points": [[70, 40], [30, 80]], "direction": "down-left"},
            {"points": [[30, 80], [70, 80]], "direction": "right"},
        ],
    },
    # Numbers
    "0": {
        "type": "number",
        "phonetic": "zero",
        "sound": "zero",
        "strokes": [
            {"points": [[50, 10], [30, 25], [30, 75], [50, 90], [70, 75], [70, 25], [50, 10]], "direction": "oval"}
        ],
    },
    "1": {
        "type": "number",
        "phonetic": "one",
        "sound": "one",
        "strokes": [
            {"points": [[35, 25], [50, 10], [50, 90]], "direction": "slant-down"},
            {"points": [[30, 90], [70, 90]], "direction": "right"},
        ],
    },
    "2": {
        "type": "number",
        "phonetic": "two",
        "sound": "two",
        "strokes": [
            {
                "points": [[30, 25], [40, 12], [60, 12], [70, 25], [70, 40], [30, 90], [70, 90]],
                "direction": "curve-down-right",
            }
        ],
    },
    "3": {
        "type": "number",
        "phonetic": "three",
        "sound": "three",
        "strokes": [
            {"points": [[30, 15], [60, 12], [70, 30], [55, 48]], "direction": "curve-right"},
            {"points": [[55, 48], [70, 65], [60, 85], [30, 88]], "direction": "curve-right"},
        ],
    },
    "4": {
        "type": "number",
        "phonetic": "four",
        "sound": "four",
        "strokes": [
            {"points": [[60, 10], [25, 60], [75, 60]], "direction": "down-right"},
            {"points": [[60, 35], [60, 90]], "direction": "down"},
        ],
    },
    "5": {
        "type": "number",
        "phonetic": "five",
        "sound": "five",
        "strokes": [
            {"points": [[65, 10], [30, 10]], "direction": "left"},
            {
                "points": [[30, 10], [30, 45], [50, 40], [68, 55], [65, 78], [45, 88], [30, 82]],
                "direction": "down-curve",
            },
        ],
    },
    "6": {
        "type": "number",
        "phonetic": "six",
        "sound": "six",
        "strokes": [
            {
                "points": [[60, 15], [45, 10], [30, 30], [30, 70], [50, 88], [68, 72], [65, 55], [45, 48], [30, 60]],
                "direction": "curve-loop",
            }
        ],
    },
    "7": {
        "type": "number",
        "phonetic": "seven",
        "sound": "seven",
        "strokes": [
            {"points": [[25, 10], [75, 10]], "direction": "right"},
            {"points": [[75, 10], [40, 90]], "direction": "down-left"},
        ],
    },
    "8": {
        "type": "number",
        "phonetic": "eight",
        "sound": "eight",
        "strokes": [
            {
                "points": [
                    [50, 50],
                    [35, 35],
                    [35, 20],
                    [50, 10],
                    [65, 20],
                    [65, 35],
                    [50, 50],
                    [30, 65],
                    [30, 78],
                    [50, 90],
                    [70, 78],
                    [70, 65],
                    [50, 50],
                ],
                "direction": "figure-8",
            }
        ],
    },
    "9": {
        "type": "number",
        "phonetic": "nine",
        "sound": "nine",
        "strokes": [
            {
                "points": [[65, 40], [50, 50], [35, 40], [35, 25], [50, 12], [65, 25], [65, 75], [50, 90], [35, 85]],
                "direction": "loop-down",
            }
        ],
    },
}


@router.get("/characters")
async def get_all_characters():
    """Get all available characters with their metadata"""
    result = {"uppercase": [], "lowercase": [], "numbers": []}

    for char, data in CHARACTERS.items():
        char_info = {"character": char, "phonetic": data["phonetic"], "sound": data["sound"]}
        if data["type"] == "uppercase":
            result["uppercase"].append(char_info)
        elif data["type"] == "lowercase":
            result["lowercase"].append(char_info)
        else:
            result["numbers"].append(char_info)

    return result


@router.get("/characters/{character}")
async def get_character(character: str):
    """Get detailed information about a specific character including stroke paths"""
    if character not in CHARACTERS:
        return {"error": "Character not found"}

    data = CHARACTERS[character]
    return {
        "character": character,
        "type": data["type"],
        "phonetic": data["phonetic"],
        "sound": data["sound"],
        "strokes": data["strokes"],
    }


@router.get("/characters/{character}/strokes")
async def get_character_strokes_endpoint(character: str, font: Optional[str] = None):
    """Get just the stroke paths for tracing a character"""
    # Try to get from font-specific JSON first
    char_data = get_character_strokes(character, font)

    # Fallback to hardcoded CHARACTERS if not found in JSON
    if char_data is None:
        if character not in CHARACTERS:
            return {"error": "Character not found"}
        char_data = CHARACTERS[character]

    return {"character": character, "strokes": char_data["strokes"], "font": font}


@router.get("/characters/{character}/guides")
async def get_character_guides(character: str, size: int = 400, font: Optional[str] = None):
    """
    Get auto-generated trace and guide images from the font.
    These are generated from the actual rendered font for perfect accuracy.
    Results are cached in the database for fast subsequent requests.
    """
    from app.services.guide_cache import get_or_generate_guide

    try:
        return get_or_generate_guide(character, size, font)
    except Exception as e:
        return {"error": f"Failed to generate guides: {str(e)}"}


@router.post("/guides/pregenerate")
async def pregenerate_guides(size: int = 400):
    """Pre-generate and cache guides for all characters"""
    from app.services.guide_cache import pregenerate_all_guides

    try:
        count = pregenerate_all_guides(size)
        return {"status": "success", "generated": count}
    except Exception as e:
        return {"error": f"Failed to pregenerate guides: {str(e)}"}


@router.delete("/guides/cache")
async def clear_guide_cache():
    """Clear all cached guides (useful when font changes)"""
    from app.services.guide_cache import clear_cache

    try:
        clear_cache()
        return {"status": "success", "message": "Cache cleared"}
    except Exception as e:
        return {"error": f"Failed to clear cache: {str(e)}"}


@router.get("/guides/stats")
async def get_guide_cache_stats():
    """Get statistics about the guide cache"""
    from app.services.guide_cache import get_cache_stats

    try:
        return get_cache_stats()
    except Exception as e:
        return {"error": f"Failed to get cache stats: {str(e)}"}


@router.get("/fonts")
async def get_fonts():
    """Get list of available fonts with metadata"""
    from app.services.trace_generator import get_available_fonts

    try:
        # Get list of font file names from trace_generator
        font_files = get_available_fonts()

        # Build response with metadata for each font
        fonts_with_metadata = []
        for font_file in font_files:
            metadata = get_font_metadata(font_file)
            if metadata:
                fonts_with_metadata.append({"name": font_file, **metadata})
            else:
                fonts_with_metadata.append(
                    {
                        "name": font_file,
                        "display_name": font_file.replace("-Regular", "").replace("-", " "),
                        "style": "Standard",
                        "description": "Standard font",
                        "characteristics": [],
                    }
                )

        return {"fonts": font_files, "fonts_detailed": fonts_with_metadata}
    except Exception as e:
        return {"error": f"Failed to get fonts: {str(e)}"}


@router.get("/fonts/{font_name}/preview")
async def get_font_preview(font_name: str, size: int = 600):
    """Get a preview image showing all characters in the specified font"""
    from app.services.trace_generator import generate_font_preview

    try:
        preview = generate_font_preview(font_name, size)
        return {"font_name": font_name, "preview": preview}
    except Exception as e:
        return {"error": f"Failed to generate font preview: {str(e)}"}


@router.get("/fonts/{font_name}.ttf")
async def get_font_file(font_name: str):
    """Serve a font file for use in the frontend"""
    # Security: only allow known font names (prevent path traversal)
    allowed_fonts = [
        "Fredoka-Regular",
        "Nunito-Regular",
        "PlaywriteUS-Regular",
        "PatrickHand-Regular",
        "Schoolbell-Regular",
    ]

    # Remove .ttf if included in font_name
    font_base = font_name.replace(".ttf", "")

    if font_base not in allowed_fonts:
        return {"error": "Font not found"}

    font_path = os.path.join(os.path.dirname(__file__), "..", "fonts", f"{font_base}.ttf")
    font_path = os.path.abspath(font_path)

    if not os.path.exists(font_path):
        return {"error": "Font file not found"}

    return FileResponse(font_path, media_type="font/ttf", filename=f"{font_base}.ttf")


@router.get("/audio/{character}")
async def get_character_audio(character: str, voice: str = "rachel"):
    """
    Get audio file for character pronunciation.
    Voice options: 'rachel' (default), 'adam', 'sarah', 'josh', or legacy 'female'/'male'
    """
    from app.services.audio_generator import DEFAULT_VOICES, ELEVENLABS_VOICES, ensure_audio_exists, get_character_data

    # Validate character
    if not get_character_data(character):
        return {"error": "Character not found"}

    # Map legacy gender values to voice names
    voice = DEFAULT_VOICES.get(voice, voice)

    # Validate voice name
    if voice not in ELEVENLABS_VOICES:
        voice = "rachel"

    try:
        audio_path = ensure_audio_exists(character, voice)
        if audio_path and os.path.exists(audio_path):
            return FileResponse(audio_path, media_type="audio/mpeg", filename=f"{character}_{voice}.mp3")
        return {"error": "Audio file not available"}
    except Exception as e:
        return {"error": f"Failed to get audio: {str(e)}"}


@router.get("/audio/{character}/info")
async def get_character_audio_info(character: str):
    """Get audio information for a character including available words"""
    from app.services.audio_generator import get_available_words, get_character_data, get_random_word

    data = get_character_data(character)
    if not data:
        return {"error": "Character not found"}

    return {
        "character": character,
        "name": data["name"],
        "type": data["type"],
        "phonetic": data["phonetic"],
        "sound": data["sound"],
        "words": get_available_words(character),
        "random_word": get_random_word(character),
    }


@router.post("/audio/generate-all")
async def generate_all_audio_files():
    """Pre-generate all audio files for both voices"""
    from app.services.audio_generator import generate_all_audio

    try:
        female_count = await generate_all_audio("female")
        male_count = await generate_all_audio("male")
        return {"status": "success", "generated": {"female": female_count, "male": male_count}}
    except Exception as e:
        return {"error": f"Failed to generate audio: {str(e)}"}


@router.get("/characters/{character}/guided-strokes")
async def get_guided_strokes(character: str, size: int = 400, font: Optional[str] = None):
    """
    Get stroke data with enhanced metadata for step-by-step guided instruction.
    Uses font-specific stroke definitions when available.
    """
    # Try to get from font-specific JSON first
    char_data = get_character_strokes(character, font)

    # Fallback to hardcoded CHARACTERS if not found in JSON
    if char_data is None:
        if character not in CHARACTERS:
            return {"error": "Character not found"}
        char_data = CHARACTERS[character]

    strokes = char_data["strokes"]
    scale = size / 100  # Convert from 0-100 to requested size
    tolerance_radius = size * 0.25  # 25% of canvas size for start/end zones (generous for kids)

    guided_strokes = []
    for i, stroke in enumerate(strokes):
        points = stroke["points"]
        direction = stroke.get("direction", "down")

        # Scale points to requested size
        scaled_points = [[p[0] * scale, p[1] * scale] for p in points]

        # Get start and end points
        start_point = scaled_points[0]
        end_point = scaled_points[-1]

        # Get kid-friendly instruction
        instruction = DIRECTION_INSTRUCTIONS.get(direction, "Follow the path from the green circle to the arrow.")

        # Assign color (cycle through colors)
        color = STROKE_COLORS[i % len(STROKE_COLORS)]

        guided_strokes.append(
            {
                "order": i + 1,
                "points": scaled_points,
                "direction": direction,
                "instruction": instruction,
                "start_zone": {"x": start_point[0], "y": start_point[1], "radius": tolerance_radius},
                "end_zone": {"x": end_point[0], "y": end_point[1], "radius": tolerance_radius},
                "color": color,
            }
        )

    return {"character": character, "total_strokes": len(strokes), "strokes": guided_strokes, "font": font}


@router.post("/characters/{character}/validate-stroke")
async def validate_stroke(character: str, request: StrokeValidationRequest):
    """
    Validate a drawn stroke against the expected stroke path.
    Returns validation result with kid-friendly feedback.
    """
    # Try to get from font-specific JSON first
    char_data = get_character_strokes(character, request.font)

    # Fallback to hardcoded CHARACTERS if not found in JSON
    if char_data is None:
        if character not in CHARACTERS:
            return {"error": "Character not found"}
        char_data = CHARACTERS[character]

    strokes: list = char_data["strokes"]  # type: ignore[assignment]

    if request.stroke_index < 0 or request.stroke_index >= len(strokes):
        return {"error": "Invalid stroke index"}

    expected_stroke: dict = strokes[request.stroke_index]
    expected_points = expected_stroke["points"]
    drawn_points = request.drawn_points

    if len(drawn_points) < 2:
        return {
            "valid": False,
            "started_correctly": False,
            "ended_correctly": False,
            "path_accuracy": 0,
            "feedback": "Try drawing a longer line!",
        }

    # Use a default size of 400 for validation (points should already be scaled)
    # We'll work in the coordinate space of the drawn points
    # Assume drawn points are in canvas coordinates (e.g., 400x400)
    # and expected points are in 0-100 space

    # Detect the scale from drawn points (approximate canvas size)
    max_coord = max(max(p[0], p[1]) for p in drawn_points)
    canvas_size = max(400, max_coord)  # Assume at least 400
    scale = canvas_size / 100

    scaled_expected = [[p[0] * scale, p[1] * scale] for p in expected_points]

    # Check start point - generous tolerance for kids
    # Apply tolerance_multiplier (0.5 = normal, 0.75 = larger, 1.0 = extra large)
    tolerance = canvas_size * 0.25 * (request.tolerance_multiplier or 1.0)
    start_expected = scaled_expected[0]
    start_drawn = drawn_points[0]
    start_distance = math.sqrt((start_drawn[0] - start_expected[0]) ** 2 + (start_drawn[1] - start_expected[1]) ** 2)
    started_correctly = start_distance <= tolerance

    # Check end point
    end_expected = scaled_expected[-1]
    end_drawn = drawn_points[-1]
    end_distance = math.sqrt((end_drawn[0] - end_expected[0]) ** 2 + (end_drawn[1] - end_expected[1]) ** 2)
    ended_correctly = end_distance <= tolerance

    # Calculate path accuracy using average distance from expected path
    def point_to_segment_distance(px, py, x1, y1, x2, y2):
        """Calculate distance from point (px, py) to line segment (x1,y1)-(x2,y2)"""
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)

    def point_to_path_distance(px, py, path_points):
        """Calculate minimum distance from point to polyline path"""
        min_dist = float("inf")
        for i in range(len(path_points) - 1):
            dist = point_to_segment_distance(
                px, py, path_points[i][0], path_points[i][1], path_points[i + 1][0], path_points[i + 1][1]
            )
            min_dist = min(min_dist, dist)
        return min_dist

    # Sample drawn points and calculate average distance to expected path
    total_distance = 0
    sample_count = min(len(drawn_points), 20)  # Sample up to 20 points
    step = max(1, len(drawn_points) // sample_count)

    actual_samples = 0
    for i in range(0, len(drawn_points), step):
        point = drawn_points[i]
        dist = point_to_path_distance(point[0], point[1], scaled_expected)
        total_distance += dist
        actual_samples += 1

    avg_distance = total_distance / max(1, actual_samples)

    # Convert distance to accuracy percentage
    # 0 distance = 100%, tolerance distance = 50%, 2*tolerance = 0%
    path_accuracy = max(0, min(100, 100 - (avg_distance / tolerance) * 50))

    # Determine if valid (started correctly, ended correctly, and decent path)
    # Very low threshold for kids - focus on start/end positions more than perfect path
    valid = started_correctly and ended_correctly and path_accuracy >= 15

    # Generate kid-friendly feedback
    if valid:
        if path_accuracy >= 80:
            feedback = "Perfect! Great job!"
        elif path_accuracy >= 60:
            feedback = "Good work! Keep practicing!"
        else:
            feedback = "Nice try! You got it!"
    else:
        if not started_correctly:
            feedback = "Start at the green circle!"
        elif not ended_correctly:
            feedback = "Try to reach the arrow at the end!"
        else:
            feedback = "Follow the dotted line more closely!"

    return {
        "valid": valid,
        "started_correctly": started_correctly,
        "ended_correctly": ended_correctly,
        "path_accuracy": round(path_accuracy, 1),
        "feedback": feedback,
    }
