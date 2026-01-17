from fastapi import APIRouter
from typing import Optional

router = APIRouter()

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
            {"points": [[50, 90], [25, 10]], "direction": "up-left"},
            {"points": [[50, 90], [75, 10]], "direction": "up-right"},
            {"points": [[35, 50], [65, 50]], "direction": "right"}
        ]
    },
    "B": {
        "type": "uppercase",
        "phonetic": "bee",
        "sound": "buh as in ball",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 10], [60, 10], [70, 25], [60, 50], [25, 50]], "direction": "right-curve"},
            {"points": [[25, 50], [65, 50], [75, 70], [65, 90], [25, 90]], "direction": "right-curve"}
        ]
    },
    "C": {
        "type": "uppercase",
        "phonetic": "see",
        "sound": "kuh as in cat",
        "strokes": [
            {"points": [[75, 20], [50, 10], [25, 30], [25, 70], [50, 90], [75, 80]], "direction": "curve-left"}
        ]
    },
    "D": {
        "type": "uppercase",
        "phonetic": "dee",
        "sound": "duh as in dog",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 10], [55, 10], [75, 30], [75, 70], [55, 90], [25, 90]], "direction": "curve-right"}
        ]
    },
    "E": {
        "type": "uppercase",
        "phonetic": "ee",
        "sound": "eh as in elephant",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 10], [75, 10]], "direction": "right"},
            {"points": [[25, 50], [65, 50]], "direction": "right"},
            {"points": [[25, 90], [75, 90]], "direction": "right"}
        ]
    },
    "F": {
        "type": "uppercase",
        "phonetic": "ef",
        "sound": "fuh as in fish",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 10], [75, 10]], "direction": "right"},
            {"points": [[25, 50], [60, 50]], "direction": "right"}
        ]
    },
    "G": {
        "type": "uppercase",
        "phonetic": "jee",
        "sound": "guh as in goat",
        "strokes": [
            {"points": [[75, 20], [50, 10], [25, 30], [25, 70], [50, 90], [75, 70], [75, 50], [55, 50]], "direction": "curve-in"}
        ]
    },
    "H": {
        "type": "uppercase",
        "phonetic": "aych",
        "sound": "huh as in hat",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[75, 10], [75, 90]], "direction": "down"},
            {"points": [[25, 50], [75, 50]], "direction": "right"}
        ]
    },
    "I": {
        "type": "uppercase",
        "phonetic": "eye",
        "sound": "ih as in igloo",
        "strokes": [
            {"points": [[35, 10], [65, 10]], "direction": "right"},
            {"points": [[50, 10], [50, 90]], "direction": "down"},
            {"points": [[35, 90], [65, 90]], "direction": "right"}
        ]
    },
    "J": {
        "type": "uppercase",
        "phonetic": "jay",
        "sound": "juh as in jump",
        "strokes": [
            {"points": [[35, 10], [65, 10]], "direction": "right"},
            {"points": [[55, 10], [55, 70], [45, 85], [30, 80]], "direction": "down-curve"}
        ]
    },
    "K": {
        "type": "uppercase",
        "phonetic": "kay",
        "sound": "kuh as in kite",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[70, 10], [25, 55]], "direction": "down-left"},
            {"points": [[40, 45], [70, 90]], "direction": "down-right"}
        ]
    },
    "L": {
        "type": "uppercase",
        "phonetic": "el",
        "sound": "luh as in lion",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 90], [75, 90]], "direction": "right"}
        ]
    },
    "M": {
        "type": "uppercase",
        "phonetic": "em",
        "sound": "muh as in moon",
        "strokes": [
            {"points": [[20, 90], [20, 10]], "direction": "up"},
            {"points": [[20, 10], [50, 50]], "direction": "down-right"},
            {"points": [[50, 50], [80, 10]], "direction": "up-right"},
            {"points": [[80, 10], [80, 90]], "direction": "down"}
        ]
    },
    "N": {
        "type": "uppercase",
        "phonetic": "en",
        "sound": "nuh as in nest",
        "strokes": [
            {"points": [[25, 90], [25, 10]], "direction": "up"},
            {"points": [[25, 10], [75, 90]], "direction": "down-right"},
            {"points": [[75, 90], [75, 10]], "direction": "up"}
        ]
    },
    "O": {
        "type": "uppercase",
        "phonetic": "oh",
        "sound": "ah as in octopus",
        "strokes": [
            {"points": [[50, 10], [25, 30], [25, 70], [50, 90], [75, 70], [75, 30], [50, 10]], "direction": "oval"}
        ]
    },
    "P": {
        "type": "uppercase",
        "phonetic": "pee",
        "sound": "puh as in pig",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 10], [60, 10], [75, 25], [75, 40], [60, 55], [25, 55]], "direction": "curve-right"}
        ]
    },
    "Q": {
        "type": "uppercase",
        "phonetic": "kyoo",
        "sound": "kwuh as in queen",
        "strokes": [
            {"points": [[50, 10], [25, 30], [25, 70], [50, 90], [75, 70], [75, 30], [50, 10]], "direction": "oval"},
            {"points": [[55, 70], [80, 95]], "direction": "down-right"}
        ]
    },
    "R": {
        "type": "uppercase",
        "phonetic": "ar",
        "sound": "ruh as in rabbit",
        "strokes": [
            {"points": [[25, 10], [25, 90]], "direction": "down"},
            {"points": [[25, 10], [60, 10], [75, 25], [60, 50], [25, 50]], "direction": "curve-right"},
            {"points": [[50, 50], [75, 90]], "direction": "down-right"}
        ]
    },
    "S": {
        "type": "uppercase",
        "phonetic": "ess",
        "sound": "sss as in snake",
        "strokes": [
            {"points": [[70, 20], [50, 10], [30, 20], [25, 35], [35, 50], [65, 55], [75, 70], [65, 85], [50, 90], [30, 85]], "direction": "s-curve"}
        ]
    },
    "T": {
        "type": "uppercase",
        "phonetic": "tee",
        "sound": "tuh as in tiger",
        "strokes": [
            {"points": [[20, 10], [80, 10]], "direction": "right"},
            {"points": [[50, 10], [50, 90]], "direction": "down"}
        ]
    },
    "U": {
        "type": "uppercase",
        "phonetic": "yoo",
        "sound": "uh as in umbrella",
        "strokes": [
            {"points": [[25, 10], [25, 70], [50, 90], [75, 70], [75, 10]], "direction": "down-curve-up"}
        ]
    },
    "V": {
        "type": "uppercase",
        "phonetic": "vee",
        "sound": "vuh as in van",
        "strokes": [
            {"points": [[20, 10], [50, 90]], "direction": "down-right"},
            {"points": [[50, 90], [80, 10]], "direction": "up-right"}
        ]
    },
    "W": {
        "type": "uppercase",
        "phonetic": "double-yoo",
        "sound": "wuh as in water",
        "strokes": [
            {"points": [[15, 10], [30, 90]], "direction": "down-right"},
            {"points": [[30, 90], [50, 40]], "direction": "up-right"},
            {"points": [[50, 40], [70, 90]], "direction": "down-right"},
            {"points": [[70, 90], [85, 10]], "direction": "up-right"}
        ]
    },
    "X": {
        "type": "uppercase",
        "phonetic": "eks",
        "sound": "ks as in box",
        "strokes": [
            {"points": [[20, 10], [80, 90]], "direction": "down-right"},
            {"points": [[80, 10], [20, 90]], "direction": "down-left"}
        ]
    },
    "Y": {
        "type": "uppercase",
        "phonetic": "why",
        "sound": "yuh as in yellow",
        "strokes": [
            {"points": [[20, 10], [50, 50]], "direction": "down-right"},
            {"points": [[80, 10], [50, 50]], "direction": "down-left"},
            {"points": [[50, 50], [50, 90]], "direction": "down"}
        ]
    },
    "Z": {
        "type": "uppercase",
        "phonetic": "zee",
        "sound": "zzz as in zebra",
        "strokes": [
            {"points": [[20, 10], [80, 10]], "direction": "right"},
            {"points": [[80, 10], [20, 90]], "direction": "down-left"},
            {"points": [[20, 90], [80, 90]], "direction": "right"}
        ]
    },
    # Lowercase letters
    "a": {
        "type": "lowercase",
        "phonetic": "ay",
        "sound": "ah as in apple",
        "strokes": [
            {"points": [[65, 40], [45, 35], [30, 45], [30, 70], [45, 80], [65, 75]], "direction": "curve-left"},
            {"points": [[65, 35], [65, 80]], "direction": "down"}
        ]
    },
    "b": {
        "type": "lowercase",
        "phonetic": "bee",
        "sound": "buh as in ball",
        "strokes": [
            {"points": [[30, 10], [30, 80]], "direction": "down"},
            {"points": [[30, 50], [45, 40], [60, 50], [60, 70], [45, 80], [30, 70]], "direction": "curve-right"}
        ]
    },
    "c": {
        "type": "lowercase",
        "phonetic": "see",
        "sound": "kuh as in cat",
        "strokes": [
            {"points": [[65, 45], [50, 35], [35, 50], [35, 65], [50, 80], [65, 70]], "direction": "curve-left"}
        ]
    },
    "d": {
        "type": "lowercase",
        "phonetic": "dee",
        "sound": "duh as in dog",
        "strokes": [
            {"points": [[65, 50], [50, 40], [35, 50], [35, 70], [50, 80], [65, 70]], "direction": "curve-left"},
            {"points": [[65, 10], [65, 80]], "direction": "down"}
        ]
    },
    "e": {
        "type": "lowercase",
        "phonetic": "ee",
        "sound": "eh as in elephant",
        "strokes": [
            {"points": [[35, 55], [65, 55]], "direction": "right"},
            {"points": [[65, 55], [65, 45], [50, 35], [35, 50], [35, 65], [50, 80], [65, 75]], "direction": "curve"}
        ]
    },
    "f": {
        "type": "lowercase",
        "phonetic": "ef",
        "sound": "fuh as in fish",
        "strokes": [
            {"points": [[60, 20], [50, 10], [40, 20], [40, 80]], "direction": "curve-down"},
            {"points": [[25, 40], [55, 40]], "direction": "right"}
        ]
    },
    "g": {
        "type": "lowercase",
        "phonetic": "jee",
        "sound": "guh as in goat",
        "strokes": [
            {"points": [[65, 50], [50, 40], [35, 50], [35, 65], [50, 75], [65, 65]], "direction": "curve-left"},
            {"points": [[65, 40], [65, 90], [50, 100], [35, 95]], "direction": "down-curve"}
        ]
    },
    "h": {
        "type": "lowercase",
        "phonetic": "aych",
        "sound": "huh as in hat",
        "strokes": [
            {"points": [[30, 10], [30, 80]], "direction": "down"},
            {"points": [[30, 50], [45, 40], [60, 50], [60, 80]], "direction": "curve-down"}
        ]
    },
    "i": {
        "type": "lowercase",
        "phonetic": "eye",
        "sound": "ih as in igloo",
        "strokes": [
            {"points": [[50, 40], [50, 80]], "direction": "down"},
            {"points": [[50, 25], [50, 28]], "direction": "dot"}
        ]
    },
    "j": {
        "type": "lowercase",
        "phonetic": "jay",
        "sound": "juh as in jump",
        "strokes": [
            {"points": [[55, 40], [55, 90], [45, 100], [35, 95]], "direction": "down-curve"},
            {"points": [[55, 25], [55, 28]], "direction": "dot"}
        ]
    },
    "k": {
        "type": "lowercase",
        "phonetic": "kay",
        "sound": "kuh as in kite",
        "strokes": [
            {"points": [[30, 10], [30, 80]], "direction": "down"},
            {"points": [[60, 40], [30, 60]], "direction": "down-left"},
            {"points": [[40, 55], [60, 80]], "direction": "down-right"}
        ]
    },
    "l": {
        "type": "lowercase",
        "phonetic": "el",
        "sound": "luh as in lion",
        "strokes": [
            {"points": [[50, 10], [50, 80]], "direction": "down"}
        ]
    },
    "m": {
        "type": "lowercase",
        "phonetic": "em",
        "sound": "muh as in moon",
        "strokes": [
            {"points": [[20, 40], [20, 80]], "direction": "down"},
            {"points": [[20, 50], [35, 40], [50, 50], [50, 80]], "direction": "curve-down"},
            {"points": [[50, 50], [65, 40], [80, 50], [80, 80]], "direction": "curve-down"}
        ]
    },
    "n": {
        "type": "lowercase",
        "phonetic": "en",
        "sound": "nuh as in nest",
        "strokes": [
            {"points": [[30, 40], [30, 80]], "direction": "down"},
            {"points": [[30, 50], [50, 40], [65, 50], [65, 80]], "direction": "curve-down"}
        ]
    },
    "o": {
        "type": "lowercase",
        "phonetic": "oh",
        "sound": "ah as in octopus",
        "strokes": [
            {"points": [[50, 35], [35, 50], [35, 65], [50, 80], [65, 65], [65, 50], [50, 35]], "direction": "oval"}
        ]
    },
    "p": {
        "type": "lowercase",
        "phonetic": "pee",
        "sound": "puh as in pig",
        "strokes": [
            {"points": [[30, 40], [30, 100]], "direction": "down"},
            {"points": [[30, 50], [45, 40], [60, 50], [60, 65], [45, 75], [30, 65]], "direction": "curve-right"}
        ]
    },
    "q": {
        "type": "lowercase",
        "phonetic": "kyoo",
        "sound": "kwuh as in queen",
        "strokes": [
            {"points": [[65, 50], [50, 40], [35, 50], [35, 65], [50, 75], [65, 65]], "direction": "curve-left"},
            {"points": [[65, 40], [65, 100]], "direction": "down"}
        ]
    },
    "r": {
        "type": "lowercase",
        "phonetic": "ar",
        "sound": "ruh as in rabbit",
        "strokes": [
            {"points": [[35, 40], [35, 80]], "direction": "down"},
            {"points": [[35, 55], [50, 42], [65, 45]], "direction": "curve-up"}
        ]
    },
    "s": {
        "type": "lowercase",
        "phonetic": "ess",
        "sound": "sss as in snake",
        "strokes": [
            {"points": [[60, 42], [50, 38], [38, 45], [40, 55], [60, 62], [62, 72], [50, 78], [38, 75]], "direction": "s-curve"}
        ]
    },
    "t": {
        "type": "lowercase",
        "phonetic": "tee",
        "sound": "tuh as in tiger",
        "strokes": [
            {"points": [[45, 15], [45, 75], [55, 80], [65, 78]], "direction": "down-curve"},
            {"points": [[30, 40], [60, 40]], "direction": "right"}
        ]
    },
    "u": {
        "type": "lowercase",
        "phonetic": "yoo",
        "sound": "uh as in umbrella",
        "strokes": [
            {"points": [[30, 40], [30, 65], [45, 78], [60, 70]], "direction": "down-curve"},
            {"points": [[60, 40], [60, 80]], "direction": "down"}
        ]
    },
    "v": {
        "type": "lowercase",
        "phonetic": "vee",
        "sound": "vuh as in van",
        "strokes": [
            {"points": [[30, 40], [50, 80]], "direction": "down-right"},
            {"points": [[50, 80], [70, 40]], "direction": "up-right"}
        ]
    },
    "w": {
        "type": "lowercase",
        "phonetic": "double-yoo",
        "sound": "wuh as in water",
        "strokes": [
            {"points": [[20, 40], [30, 80]], "direction": "down-right"},
            {"points": [[30, 80], [45, 55]], "direction": "up-right"},
            {"points": [[45, 55], [60, 80]], "direction": "down-right"},
            {"points": [[60, 80], [75, 40]], "direction": "up-right"}
        ]
    },
    "x": {
        "type": "lowercase",
        "phonetic": "eks",
        "sound": "ks as in box",
        "strokes": [
            {"points": [[30, 40], [70, 80]], "direction": "down-right"},
            {"points": [[70, 40], [30, 80]], "direction": "down-left"}
        ]
    },
    "y": {
        "type": "lowercase",
        "phonetic": "why",
        "sound": "yuh as in yellow",
        "strokes": [
            {"points": [[30, 40], [50, 70]], "direction": "down-right"},
            {"points": [[70, 40], [50, 70], [40, 90], [30, 95]], "direction": "down-curve"}
        ]
    },
    "z": {
        "type": "lowercase",
        "phonetic": "zee",
        "sound": "zzz as in zebra",
        "strokes": [
            {"points": [[30, 40], [70, 40]], "direction": "right"},
            {"points": [[70, 40], [30, 80]], "direction": "down-left"},
            {"points": [[30, 80], [70, 80]], "direction": "right"}
        ]
    },
    # Numbers
    "0": {
        "type": "number",
        "phonetic": "zero",
        "sound": "zero",
        "strokes": [
            {"points": [[50, 10], [30, 25], [30, 75], [50, 90], [70, 75], [70, 25], [50, 10]], "direction": "oval"}
        ]
    },
    "1": {
        "type": "number",
        "phonetic": "one",
        "sound": "one",
        "strokes": [
            {"points": [[35, 25], [50, 10], [50, 90]], "direction": "slant-down"},
            {"points": [[30, 90], [70, 90]], "direction": "right"}
        ]
    },
    "2": {
        "type": "number",
        "phonetic": "two",
        "sound": "two",
        "strokes": [
            {"points": [[30, 25], [40, 12], [60, 12], [70, 25], [70, 40], [30, 90], [70, 90]], "direction": "curve-down-right"}
        ]
    },
    "3": {
        "type": "number",
        "phonetic": "three",
        "sound": "three",
        "strokes": [
            {"points": [[30, 15], [60, 12], [70, 30], [55, 48]], "direction": "curve-right"},
            {"points": [[55, 48], [70, 65], [60, 85], [30, 88]], "direction": "curve-right"}
        ]
    },
    "4": {
        "type": "number",
        "phonetic": "four",
        "sound": "four",
        "strokes": [
            {"points": [[60, 10], [25, 60], [75, 60]], "direction": "down-right"},
            {"points": [[60, 35], [60, 90]], "direction": "down"}
        ]
    },
    "5": {
        "type": "number",
        "phonetic": "five",
        "sound": "five",
        "strokes": [
            {"points": [[65, 10], [30, 10]], "direction": "left"},
            {"points": [[30, 10], [30, 45], [50, 40], [68, 55], [65, 78], [45, 88], [30, 82]], "direction": "down-curve"}
        ]
    },
    "6": {
        "type": "number",
        "phonetic": "six",
        "sound": "six",
        "strokes": [
            {"points": [[60, 15], [45, 10], [30, 30], [30, 70], [50, 88], [68, 72], [65, 55], [45, 48], [30, 60]], "direction": "curve-loop"}
        ]
    },
    "7": {
        "type": "number",
        "phonetic": "seven",
        "sound": "seven",
        "strokes": [
            {"points": [[25, 10], [75, 10]], "direction": "right"},
            {"points": [[75, 10], [40, 90]], "direction": "down-left"}
        ]
    },
    "8": {
        "type": "number",
        "phonetic": "eight",
        "sound": "eight",
        "strokes": [
            {"points": [[50, 50], [35, 35], [35, 20], [50, 10], [65, 20], [65, 35], [50, 50], [30, 65], [30, 78], [50, 90], [70, 78], [70, 65], [50, 50]], "direction": "figure-8"}
        ]
    },
    "9": {
        "type": "number",
        "phonetic": "nine",
        "sound": "nine",
        "strokes": [
            {"points": [[65, 40], [50, 50], [35, 40], [35, 25], [50, 12], [65, 25], [65, 75], [50, 90], [35, 85]], "direction": "loop-down"}
        ]
    }
}


@router.get("/characters")
async def get_all_characters():
    """Get all available characters with their metadata"""
    result = {
        "uppercase": [],
        "lowercase": [],
        "numbers": []
    }

    for char, data in CHARACTERS.items():
        char_info = {
            "character": char,
            "phonetic": data["phonetic"],
            "sound": data["sound"]
        }
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
        "strokes": data["strokes"]
    }


@router.get("/characters/{character}/strokes")
async def get_character_strokes(character: str):
    """Get just the stroke paths for tracing a character"""
    if character not in CHARACTERS:
        return {"error": "Character not found"}

    return {
        "character": character,
        "strokes": CHARACTERS[character]["strokes"]
    }
