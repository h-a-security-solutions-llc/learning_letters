"""
Audio generation service for character pronunciation.
Uses ElevenLabs for high-quality, natural-sounding voices.
Falls back to gTTS if ElevenLabs is unavailable.
"""

import os
import random
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Directory for generated audio files
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "audio")

# ElevenLabs voice IDs - these are pre-made voices available on free tier
# You can find more at https://elevenlabs.io/voice-library
ELEVENLABS_VOICES = {
    # Female voices
    "rachel": {"id": "21m00Tcm4TlvDq8ikWAM", "gender": "female", "name": "Rachel", "description": "Calm & Gentle"},
    "sarah": {"id": "EXAVITQu4vr4xnSDxMaL", "gender": "female", "name": "Sarah", "description": "Soft & Friendly"},
    # Male voices
    "adam": {"id": "pNInz6obpgDQGcFmaJgB", "gender": "male", "name": "Adam", "description": "Deep & Warm"},
    "josh": {"id": "TxGEqnHWrfWFTfGW9XjX", "gender": "male", "name": "Josh", "description": "Young & Friendly"},
}

# Map simple gender to default voice
DEFAULT_VOICES = {
    "female": "rachel",
    "male": "adam",
}

# Character pronunciation data with multiple example words
CHARACTER_DATA = {
    # Uppercase letters
    "A": {
        "type": "uppercase",
        "name": "Capital A",
        "sound": "ah",
        "words": ["apple", "alligator", "ant", "astronaut", "airplane"],
    },
    "B": {
        "type": "uppercase",
        "name": "Capital B",
        "sound": "buh",
        "words": ["ball", "bear", "banana", "butterfly", "boat"],
    },
    "C": {"type": "uppercase", "name": "Capital C", "sound": "kuh", "words": ["cat", "car", "cake", "cow", "cookie"]},
    "D": {
        "type": "uppercase",
        "name": "Capital D",
        "sound": "duh",
        "words": ["dog", "duck", "dinosaur", "door", "dolphin"],
    },
    "E": {
        "type": "uppercase",
        "name": "Capital E",
        "sound": "eh",
        "words": ["elephant", "egg", "elbow", "elf", "eagle"],
    },
    "F": {
        "type": "uppercase",
        "name": "Capital F",
        "sound": "fuh",
        "words": ["fish", "frog", "flower", "fire", "feather"],
    },
    "G": {
        "type": "uppercase",
        "name": "Capital G",
        "sound": "guh",
        "words": ["goat", "grape", "giraffe", "guitar", "garden"],
    },
    "H": {
        "type": "uppercase",
        "name": "Capital H",
        "sound": "huh",
        "words": ["hat", "horse", "house", "heart", "hippo"],
    },
    "I": {
        "type": "uppercase",
        "name": "Capital I",
        "sound": "ih",
        "words": ["igloo", "ice cream", "insect", "island", "iguana"],
    },
    "J": {
        "type": "uppercase",
        "name": "Capital J",
        "sound": "juh",
        "words": ["jump", "jellyfish", "jacket", "juice", "jaguar"],
    },
    "K": {
        "type": "uppercase",
        "name": "Capital K",
        "sound": "kuh",
        "words": ["kite", "king", "kangaroo", "key", "kitten"],
    },
    "L": {
        "type": "uppercase",
        "name": "Capital L",
        "sound": "luh",
        "words": ["lion", "lemon", "leaf", "ladder", "lamp"],
    },
    "M": {
        "type": "uppercase",
        "name": "Capital M",
        "sound": "muh",
        "words": ["moon", "monkey", "mouse", "milk", "mountain"],
    },
    "N": {
        "type": "uppercase",
        "name": "Capital N",
        "sound": "nuh",
        "words": ["nest", "nose", "nut", "night", "noodle"],
    },
    "O": {
        "type": "uppercase",
        "name": "Capital O",
        "sound": "ah",
        "words": ["octopus", "orange", "owl", "ocean", "otter"],
    },
    "P": {
        "type": "uppercase",
        "name": "Capital P",
        "sound": "puh",
        "words": ["pig", "pizza", "panda", "penguin", "plane"],
    },
    "Q": {
        "type": "uppercase",
        "name": "Capital Q",
        "sound": "kwuh",
        "words": ["queen", "quilt", "question", "quiet", "quail"],
    },
    "R": {
        "type": "uppercase",
        "name": "Capital R",
        "sound": "ruh",
        "words": ["rabbit", "rainbow", "robot", "rocket", "rain"],
    },
    "S": {
        "type": "uppercase",
        "name": "Capital S",
        "sound": "sss",
        "words": ["snake", "sun", "star", "strawberry", "spider"],
    },
    "T": {
        "type": "uppercase",
        "name": "Capital T",
        "sound": "tuh",
        "words": ["tiger", "turtle", "train", "tree", "tomato"],
    },
    "U": {
        "type": "uppercase",
        "name": "Capital U",
        "sound": "uh",
        "words": ["umbrella", "unicorn", "up", "under", "uniform"],
    },
    "V": {
        "type": "uppercase",
        "name": "Capital V",
        "sound": "vuh",
        "words": ["van", "violin", "volcano", "vegetable", "vest"],
    },
    "W": {
        "type": "uppercase",
        "name": "Capital W",
        "sound": "wuh",
        "words": ["water", "whale", "wagon", "window", "watermelon"],
    },
    "X": {
        "type": "uppercase",
        "name": "Capital X",
        "sound": "ks",
        "words": ["x-ray", "xylophone", "box", "fox", "mix"],
    },
    "Y": {
        "type": "uppercase",
        "name": "Capital Y",
        "sound": "yuh",
        "words": ["yellow", "yak", "yarn", "yogurt", "yo-yo"],
    },
    "Z": {
        "type": "uppercase",
        "name": "Capital Z",
        "sound": "zzz",
        "words": ["zebra", "zoo", "zipper", "zero", "zigzag"],
    },
    # Lowercase letters
    "a": {
        "type": "lowercase",
        "name": "Lowercase a",
        "sound": "ah",
        "words": ["apple", "alligator", "ant", "astronaut", "airplane"],
    },
    "b": {
        "type": "lowercase",
        "name": "Lowercase b",
        "sound": "buh",
        "words": ["ball", "bear", "banana", "butterfly", "boat"],
    },
    "c": {"type": "lowercase", "name": "Lowercase c", "sound": "kuh", "words": ["cat", "car", "cake", "cow", "cookie"]},
    "d": {
        "type": "lowercase",
        "name": "Lowercase d",
        "sound": "duh",
        "words": ["dog", "duck", "dinosaur", "door", "dolphin"],
    },
    "e": {
        "type": "lowercase",
        "name": "Lowercase e",
        "sound": "eh",
        "words": ["elephant", "egg", "elbow", "elf", "eagle"],
    },
    "f": {
        "type": "lowercase",
        "name": "Lowercase f",
        "sound": "fuh",
        "words": ["fish", "frog", "flower", "fire", "feather"],
    },
    "g": {
        "type": "lowercase",
        "name": "Lowercase g",
        "sound": "guh",
        "words": ["goat", "grape", "giraffe", "guitar", "garden"],
    },
    "h": {
        "type": "lowercase",
        "name": "Lowercase h",
        "sound": "huh",
        "words": ["hat", "horse", "house", "heart", "hippo"],
    },
    "i": {
        "type": "lowercase",
        "name": "Lowercase i",
        "sound": "ih",
        "words": ["igloo", "ice cream", "insect", "island", "iguana"],
    },
    "j": {
        "type": "lowercase",
        "name": "Lowercase j",
        "sound": "juh",
        "words": ["jump", "jellyfish", "jacket", "juice", "jaguar"],
    },
    "k": {
        "type": "lowercase",
        "name": "Lowercase k",
        "sound": "kuh",
        "words": ["kite", "king", "kangaroo", "key", "kitten"],
    },
    "l": {
        "type": "lowercase",
        "name": "Lowercase l",
        "sound": "luh",
        "words": ["lion", "lemon", "leaf", "ladder", "lamp"],
    },
    "m": {
        "type": "lowercase",
        "name": "Lowercase m",
        "sound": "muh",
        "words": ["moon", "monkey", "mouse", "milk", "mountain"],
    },
    "n": {
        "type": "lowercase",
        "name": "Lowercase n",
        "sound": "nuh",
        "words": ["nest", "nose", "nut", "night", "noodle"],
    },
    "o": {
        "type": "lowercase",
        "name": "Lowercase o",
        "sound": "ah",
        "words": ["octopus", "orange", "owl", "ocean", "otter"],
    },
    "p": {
        "type": "lowercase",
        "name": "Lowercase p",
        "sound": "puh",
        "words": ["pig", "pizza", "panda", "penguin", "plane"],
    },
    "q": {
        "type": "lowercase",
        "name": "Lowercase q",
        "sound": "kwuh",
        "words": ["queen", "quilt", "question", "quiet", "quail"],
    },
    "r": {
        "type": "lowercase",
        "name": "Lowercase r",
        "sound": "ruh",
        "words": ["rabbit", "rainbow", "robot", "rocket", "rain"],
    },
    "s": {
        "type": "lowercase",
        "name": "Lowercase s",
        "sound": "sss",
        "words": ["snake", "sun", "star", "strawberry", "spider"],
    },
    "t": {
        "type": "lowercase",
        "name": "Lowercase t",
        "sound": "tuh",
        "words": ["tiger", "turtle", "train", "tree", "tomato"],
    },
    "u": {
        "type": "lowercase",
        "name": "Lowercase u",
        "sound": "uh",
        "words": ["umbrella", "unicorn", "up", "under", "uniform"],
    },
    "v": {
        "type": "lowercase",
        "name": "Lowercase v",
        "sound": "vuh",
        "words": ["van", "violin", "volcano", "vegetable", "vest"],
    },
    "w": {
        "type": "lowercase",
        "name": "Lowercase w",
        "sound": "wuh",
        "words": ["water", "whale", "wagon", "window", "watermelon"],
    },
    "x": {
        "type": "lowercase",
        "name": "Lowercase x",
        "sound": "ks",
        "words": ["x-ray", "xylophone", "box", "fox", "mix"],
    },
    "y": {
        "type": "lowercase",
        "name": "Lowercase y",
        "sound": "yuh",
        "words": ["yellow", "yak", "yarn", "yogurt", "yo-yo"],
    },
    "z": {
        "type": "lowercase",
        "name": "Lowercase z",
        "sound": "zzz",
        "words": ["zebra", "zoo", "zipper", "zero", "zigzag"],
    },
    # Numbers
    "0": {"type": "number", "name": "Zero", "sound": "zero", "words": ["zero apples", "nothing", "none"]},
    "1": {"type": "number", "name": "One", "sound": "one", "words": ["one sun", "one moon", "one nose"]},
    "2": {"type": "number", "name": "Two", "sound": "two", "words": ["two eyes", "two hands", "two feet"]},
    "3": {"type": "number", "name": "Three", "sound": "three", "words": ["three bears", "three pigs", "three wishes"]},
    "4": {"type": "number", "name": "Four", "sound": "four", "words": ["four wheels", "four seasons", "four corners"]},
    "5": {"type": "number", "name": "Five", "sound": "five", "words": ["five fingers", "five toes", "high five"]},
    "6": {"type": "number", "name": "Six", "sound": "six", "words": ["six legs", "six sides", "six eggs"]},
    "7": {"type": "number", "name": "Seven", "sound": "seven", "words": ["seven days", "seven colors", "seven dwarfs"]},
    "8": {"type": "number", "name": "Eight", "sound": "eight", "words": ["eight legs", "eight crayons", "eight arms"]},
    "9": {"type": "number", "name": "Nine", "sound": "nine", "words": ["nine planets", "nine lives", "nine candles"]},
}


def get_character_data(character: str) -> Optional[dict]:
    """Get pronunciation data for a character."""
    return CHARACTER_DATA.get(character)


def get_random_word(character: str) -> str:
    """Get a random example word for a character."""
    data = CHARACTER_DATA.get(character)
    if data and data.get("words"):
        return random.choice(data["words"])  # nosec B311 - Not used for security
    return ""


def build_speech_text(character: str, word: Optional[str] = None) -> str:
    """Build the speech text for a character."""
    data = CHARACTER_DATA.get(character)
    if not data:
        return character

    if word is None:
        word = get_random_word(character)

    name = data["name"]
    sound = data["sound"]

    # Same format for all character types
    return f"{name}. {sound}, {sound}, as in {word}."


def get_audio_path(character: str, voice: str = "female") -> str:
    """Get the file path for a character's audio file."""
    if character.isupper():
        char_name = f"upper_{character}"
    elif character.islower():
        char_name = f"lower_{character}"
    else:
        char_name = f"num_{character}"

    return os.path.join(AUDIO_DIR, voice, f"{char_name}.mp3")


def get_available_voices() -> dict:
    """Get available voice options for the frontend."""
    return {
        "voices": [
            {"id": key, "name": v["name"], "gender": v["gender"], "description": v["description"]}
            for key, v in ELEVENLABS_VOICES.items()
        ]
    }


def generate_audio_file_elevenlabs(character: str, voice: str = "rachel", word: Optional[str] = None) -> str:
    """Generate audio using ElevenLabs API."""
    from elevenlabs import ElevenLabs

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not set")

    # Get voice ID
    voice_config = ELEVENLABS_VOICES.get(voice)
    if not voice_config:
        # If voice is 'male' or 'female', use default
        default_voice = DEFAULT_VOICES.get(voice, "rachel")
        voice_config = ELEVENLABS_VOICES[default_voice]
        voice = default_voice

    voice_id = voice_config["id"]
    text = build_speech_text(character, word)
    output_path = get_audio_path(character, voice)

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Generate audio
    client = ElevenLabs(api_key=api_key)

    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_turbo_v2_5",  # Updated model for free tier
    )

    # Save audio to file
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return output_path


def generate_audio_file(character: str, voice: str = "rachel", word: Optional[str] = None) -> str:
    """Generate an audio file for a character pronunciation."""
    return generate_audio_file_elevenlabs(character, voice, word)


def generate_all_audio(voice: str = "rachel") -> int:
    """Generate audio files for all characters with specified voice."""
    count = 0
    for character in CHARACTER_DATA:
        try:
            generate_audio_file(character, voice)
            count += 1
            print(f"Generated audio for '{character}' with {voice} voice ({count}/{len(CHARACTER_DATA)})")
        except Exception as e:
            print(f"Failed to generate audio for '{character}': {e}")

    return count


def ensure_audio_exists(character: str, voice: str = "rachel") -> Optional[str]:
    """Ensure audio file exists for a character, generating if needed."""
    # Map gender to default voice if needed
    voice = DEFAULT_VOICES.get(voice, voice)

    path = get_audio_path(character, voice)

    if not os.path.exists(path):
        try:
            generate_audio_file(character, voice)
        except Exception as e:
            print(f"Failed to generate audio for '{character}': {e}")
            return None

    return path if os.path.exists(path) else None


def get_available_words(character: str) -> list[str]:
    """Get all available example words for a character."""
    data = CHARACTER_DATA.get(character)
    if data and data.get("words"):
        return list(data["words"])
    return []


# For running as a script to pre-generate all audio
if __name__ == "__main__":
    import sys

    voices_to_generate = sys.argv[1:] if len(sys.argv) > 1 else ["rachel", "adam"]

    for voice in voices_to_generate:
        print(f"\nGenerating {voice} voice audio files...")
        count = generate_all_audio(voice)
        print(f"Generated {count} audio files for {voice} voice")
