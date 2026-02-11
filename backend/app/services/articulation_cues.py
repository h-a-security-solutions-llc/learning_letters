"""
Articulation cues for teaching letter sounds.

Based on research from:
- Cued Articulation (Jane Passy)
- Lindamood-Bell LiPS Program
- Jolly Phonics
- Fundations (Wilson Reading)

These cues help students understand HOW to physically produce each sound,
which is especially helpful for students who struggle with phonemic awareness.
"""

from typing import Optional

# Sound classification data
# Maps the base sound to its articulation information
SOUND_CUES = {
    # === VOWELS (Short sounds for kindergarten) ===
    "short_a": {
        "phoneme": "/æ/",
        "sound_type": "vowel",
        "voiced": True,
        "lips_label": "Open Mouth",  # LiPS-style label
        "mouth_position": "Open mouth wide, tongue low and flat, jaw drops down",
        "hand_cue": "Drop jaw with hand, or tap open palm downward",
        "body_cue": "Open mouth wide like at the doctor saying 'ahh'",
        "teaching_tip": "Have child look in mirror - mouth should be open wide enough to fit two fingers stacked",
        "common_errors": ["Saying 'uh' instead of 'ah'", "Not opening mouth wide enough"],
        "feel_it": "Feel your jaw drop down and your mouth open wide",
        "visual_description": "Mouth wide open, tongue flat on bottom of mouth",
    },
    "short_e": {
        "phoneme": "/ɛ/",
        "sound_type": "vowel",
        "voiced": True,
        "lips_label": "Open Mouth",
        "mouth_position": "Mouth slightly open, tongue middle-high, corners of mouth slightly back",
        "hand_cue": "Hand flat, palm down, at mid-level",
        "body_cue": "Smile slightly while making the sound",
        "teaching_tip": "Like the beginning of 'egg' - mouth not as wide as 'ah'",
        "common_errors": ["Confusing with short 'i'", "Making it too long"],
        "feel_it": "Feel your tongue rise slightly in the middle of your mouth",
        "visual_description": "Mouth partially open, relaxed smile shape",
    },
    "short_i": {
        "phoneme": "/ɪ/",
        "sound_type": "vowel",
        "voiced": True,
        "lips_label": "Open Mouth",
        "mouth_position": "Mouth slightly open, tongue high, lips relaxed",
        "hand_cue": "Wiggle fingers at end of nose like mouse whiskers",
        "body_cue": "Pretend to be a mouse - 'ih ih ih'",
        "teaching_tip": "Quick, short sound - like the squeak of a mouse",
        "common_errors": ["Making it sound like 'ee'", "Holding the sound too long"],
        "feel_it": "Feel your tongue rise up toward the roof of your mouth",
        "visual_description": "Small mouth opening, tongue raised",
    },
    "short_o": {
        "phoneme": "/ɒ/",
        "sound_type": "vowel",
        "voiced": True,
        "lips_label": "Open Mouth",
        "mouth_position": "Mouth open and rounded, tongue low and back",
        "hand_cue": "Make an 'O' shape with hand or fingers",
        "body_cue": "Make your mouth into an 'O' shape",
        "teaching_tip": "Round your lips like you're going to say 'oh' but make it short",
        "common_errors": ["Confusing with 'ah' sound", "Making lips too tight"],
        "feel_it": "Feel your lips round into a circle shape",
        "visual_description": "Rounded lips forming an O shape, mouth moderately open",
    },
    "short_u": {
        "phoneme": "/ʌ/",
        "sound_type": "vowel",
        "voiced": True,
        "lips_label": "Open Mouth",
        "mouth_position": "Mouth relaxed and slightly open, tongue in middle",
        "hand_cue": "Push hand up from stomach (like being punched - 'uh!')",
        "body_cue": "Like a quick grunt or being surprised",
        "teaching_tip": "The most relaxed vowel - mouth barely open, very short",
        "common_errors": ["Holding it too long", "Confusing with 'ah'"],
        "feel_it": "Feel your mouth stay relaxed, barely moving",
        "visual_description": "Relaxed mouth, slightly open, neutral position",
    },

    # === STOP CONSONANTS (Lip Poppers, Tip Tappers, Tongue Scrapers) ===
    "p": {
        "phoneme": "/p/",
        "sound_type": "stop",
        "voiced": False,
        "lips_label": "Lip Popper",  # LiPS label
        "mouth_position": "Lips pressed together, then pop apart with a puff of air",
        "hand_cue": "One finger pops up from closed fist (voiceless = 1 finger)",
        "body_cue": "Hold paper in front of mouth - it should move when you make the sound",
        "teaching_tip": "Lips start together and POP apart. No voice - just air!",
        "common_errors": ["Adding 'uh' after (saying 'puh')", "Using voice (making it sound like 'b')"],
        "feel_it": "Feel your lips press together then pop apart. Feel the puff of air on your hand.",
        "visual_description": "Lips pressed firmly together, then burst open",
        "throat_vibration": False,
    },
    "b": {
        "phoneme": "/b/",
        "sound_type": "stop",
        "voiced": True,
        "lips_label": "Lip Popper",
        "mouth_position": "Lips pressed together, then pop apart with voice",
        "hand_cue": "Two fingers pop up from closed fist (voiced = 2 fingers)",
        "body_cue": "Touch your throat - feel the vibration (voice box buzzing)",
        "teaching_tip": "Same as /p/ but with your voice ON. Feel your throat buzz!",
        "common_errors": ["Adding 'uh' after (saying 'buh')", "Not using voice"],
        "feel_it": "Feel your lips pop AND your throat vibrate at the same time",
        "visual_description": "Lips pressed together then pop open, throat vibrates",
        "throat_vibration": True,
    },
    "t": {
        "phoneme": "/t/",
        "sound_type": "stop",
        "voiced": False,
        "lips_label": "Tip Tapper",
        "mouth_position": "Tongue tip taps the bumpy ridge behind top teeth, then releases",
        "hand_cue": "One finger taps other palm quickly",
        "body_cue": "Turn head side to side like watching tennis, say 't t t'",
        "teaching_tip": "Quick tap with tongue tip on the ridge behind your teeth. No voice!",
        "common_errors": ["Adding 'uh' after", "Tongue touching teeth instead of ridge"],
        "feel_it": "Feel your tongue tip tap the bumpy spot behind your top teeth",
        "visual_description": "Tongue tip touches ridge behind upper teeth briefly",
        "throat_vibration": False,
    },
    "d": {
        "phoneme": "/d/",
        "sound_type": "stop",
        "voiced": True,
        "lips_label": "Tip Tapper",
        "mouth_position": "Tongue tip taps the bumpy ridge behind top teeth with voice",
        "hand_cue": "Two fingers tap other palm",
        "body_cue": "Touch throat while making sound - feel the buzz",
        "teaching_tip": "Same as /t/ but with your voice ON. Tongue taps + throat buzzes!",
        "common_errors": ["Adding 'uh' after", "Not using voice"],
        "feel_it": "Feel your tongue tap AND your throat vibrate together",
        "visual_description": "Tongue tip touches ridge behind upper teeth, throat vibrates",
        "throat_vibration": True,
    },
    "k": {
        "phoneme": "/k/",
        "sound_type": "stop",
        "voiced": False,
        "lips_label": "Tongue Scraper",
        "mouth_position": "Back of tongue pushes up against soft palate (back of roof of mouth), then releases",
        "hand_cue": "One finger makes clicking motion, or raise hands like cat claws",
        "body_cue": "Feel the back of your tongue touch the roof of your mouth",
        "teaching_tip": "Sound comes from the BACK of your mouth. Like a quiet cough!",
        "common_errors": ["Adding 'uh' after", "Making it in the front of mouth"],
        "feel_it": "Feel the back of your tongue bump up against the back of the roof of your mouth",
        "visual_description": "Back of tongue raises to touch soft palate, mouth slightly open",
        "throat_vibration": False,
    },
    "g": {
        "phoneme": "/g/",
        "sound_type": "stop",
        "voiced": True,
        "lips_label": "Tongue Scraper",
        "mouth_position": "Back of tongue pushes up against soft palate with voice",
        "hand_cue": "Two fingers spiral down like water in drain",
        "body_cue": "Touch throat - feel the buzz while back of tongue touches roof",
        "teaching_tip": "Same spot as /k/ but with voice ON. Back of tongue + throat buzz!",
        "common_errors": ["Adding 'uh' after", "Not using voice"],
        "feel_it": "Feel the back of your tongue bump up AND your throat vibrate",
        "visual_description": "Back of tongue raises to soft palate, throat vibrates",
        "throat_vibration": True,
    },

    # === FRICATIVES (Continuous sounds - Lip Coolers, Tongue Coolers, Skinny/Fat Sounds) ===
    "f": {
        "phoneme": "/f/",
        "sound_type": "fricative",
        "voiced": False,
        "lips_label": "Lip Cooler",
        "mouth_position": "Top teeth rest gently on lower lip, blow air out",
        "hand_cue": "Flowing motion with one finger, like air streaming out",
        "body_cue": "Put finger in front of mouth - feel the cool air on your finger",
        "teaching_tip": "Teeth on lip, blow air. The air should feel cool on your finger!",
        "common_errors": ["Biting lip too hard", "Adding voice (making 'v')"],
        "feel_it": "Feel your top teeth touch your bottom lip and cool air flow out",
        "visual_description": "Upper teeth resting on lower lip, air flowing through",
        "throat_vibration": False,
    },
    "v": {
        "phoneme": "/v/",
        "sound_type": "fricative",
        "voiced": True,
        "lips_label": "Lip Cooler",
        "mouth_position": "Top teeth rest gently on lower lip, blow air out with voice",
        "hand_cue": "Flowing motion with two fingers",
        "body_cue": "Feel throat vibrate while teeth are on lip",
        "teaching_tip": "Same as /f/ but turn your voice ON. Teeth on lip + throat buzz!",
        "common_errors": ["Not using voice", "Teeth not touching lip"],
        "feel_it": "Feel your teeth on your lip AND your throat vibrating",
        "visual_description": "Upper teeth on lower lip, air flowing, throat vibrates",
        "throat_vibration": True,
    },
    "s": {
        "phoneme": "/s/",
        "sound_type": "fricative",
        "voiced": False,
        "lips_label": "Skinny Sound",
        "mouth_position": "Teeth close together, tongue behind teeth, blow thin stream of air",
        "hand_cue": "Weave hand in S shape like a snake",
        "body_cue": "Make a snake sound - 'sssssss'",
        "teaching_tip": "Teeth together, skinny stream of air. Like a hissing snake!",
        "common_errors": ["Tongue sticking out (making 'th')", "Teeth too far apart"],
        "feel_it": "Feel the thin stream of air flowing between your teeth",
        "visual_description": "Teeth close together, small opening for air, tongue behind teeth",
        "throat_vibration": False,
    },
    "z": {
        "phoneme": "/z/",
        "sound_type": "fricative",
        "voiced": True,
        "lips_label": "Skinny Sound",
        "mouth_position": "Same as /s/ but with voice - teeth close, blow air with voice",
        "hand_cue": "Weave hand in Z shape like a buzzing bee",
        "body_cue": "Make a buzzing bee sound - 'zzzzzz'",
        "teaching_tip": "Same as snake sound but turn voice ON. Like a buzzing bee!",
        "common_errors": ["Not using voice", "Tongue sticking out"],
        "feel_it": "Feel the buzzing in your throat while air flows through teeth",
        "visual_description": "Teeth close together, air flowing, throat vibrates",
        "throat_vibration": True,
    },
    "h": {
        "phoneme": "/h/",
        "sound_type": "fricative",
        "voiced": False,
        "lips_label": "Windy Sound",
        "mouth_position": "Mouth open, push air out from throat - like a quiet breath",
        "hand_cue": "Hand in front of mouth, push air out",
        "body_cue": "Pant like a tired dog, or pretend to fog up a mirror",
        "teaching_tip": "Just a puff of air from your throat. Mouth stays open!",
        "common_errors": ["Making it too strong", "Adding voice"],
        "feel_it": "Feel the warm air coming from deep in your throat",
        "visual_description": "Mouth open, breath of air from throat",
        "throat_vibration": False,
    },
    "th_voiceless": {
        "phoneme": "/θ/",
        "sound_type": "fricative",
        "voiced": False,
        "lips_label": "Tongue Cooler",
        "mouth_position": "Tongue tip sticks out slightly between teeth, blow air over tongue",
        "hand_cue": "Tongue gesture with one finger pointing out",
        "body_cue": "Stick tongue out slightly and blow - feel cool air on tongue",
        "teaching_tip": "Stick tongue out just a little, blow air. Tongue gets cool!",
        "common_errors": ["Saying 'f' instead", "Tongue not sticking out"],
        "feel_it": "Feel the cool air flowing over your tongue tip",
        "visual_description": "Tongue tip visible between teeth, air flowing",
        "throat_vibration": False,
    },
    "th_voiced": {
        "phoneme": "/ð/",
        "sound_type": "fricative",
        "voiced": True,
        "lips_label": "Tongue Cooler",
        "mouth_position": "Tongue tip between teeth with voice",
        "hand_cue": "Tongue gesture with two fingers",
        "body_cue": "Same as voiceless 'th' but feel throat buzz",
        "teaching_tip": "Tongue out + voice ON. Used in 'the', 'this', 'that'",
        "common_errors": ["Saying 'v' instead", "Not using voice"],
        "feel_it": "Feel your tongue between teeth AND throat vibrating",
        "visual_description": "Tongue between teeth, throat vibrates",
        "throat_vibration": True,
    },
    "sh": {
        "phoneme": "/ʃ/",
        "sound_type": "fricative",
        "voiced": False,
        "lips_label": "Fat Sound",
        "mouth_position": "Lips pushed forward and rounded, tongue pulled back, wide stream of air",
        "hand_cue": "Finger to lips in 'quiet' gesture",
        "body_cue": "Tell someone to be quiet - 'shhhh'",
        "teaching_tip": "Push lips out like a fish, wide stream of air. Be quiet sound!",
        "common_errors": ["Making 's' instead", "Lips not rounded"],
        "feel_it": "Feel your lips push forward and the wide stream of air",
        "visual_description": "Lips rounded and pushed forward, tongue pulled back",
        "throat_vibration": False,
    },

    # === NASALS (Nose Sounds) ===
    "m": {
        "phoneme": "/m/",
        "sound_type": "nasal",
        "voiced": True,
        "lips_label": "Nose Sound",
        "mouth_position": "Lips together, sound comes out your nose",
        "hand_cue": "Rub tummy - 'mmmm' like yummy food",
        "body_cue": "Hold nose while trying to make sound - it stops!",
        "teaching_tip": "Lips together, hum through your nose. Yummy sound!",
        "common_errors": ["Opening lips", "Not humming through nose"],
        "feel_it": "Feel your lips together AND feel vibration in your nose",
        "visual_description": "Lips pressed together, sound resonates through nose",
        "throat_vibration": True,
        "nose_vibration": True,
    },
    "n": {
        "phoneme": "/n/",
        "sound_type": "nasal",
        "voiced": True,
        "lips_label": "Nose Sound",
        "mouth_position": "Tongue tip on ridge behind teeth, sound comes out nose",
        "hand_cue": "Point to nose while making sound",
        "body_cue": "Hold nose while trying - it stops! Sound goes through nose",
        "teaching_tip": "Tongue on the spot behind your teeth, hum through nose",
        "common_errors": ["Tongue not in right spot", "Letting air out mouth"],
        "feel_it": "Feel your tongue tip touch the ridge AND vibration in your nose",
        "visual_description": "Tongue tip behind upper teeth, sound through nose",
        "throat_vibration": True,
        "nose_vibration": True,
    },
    "ng": {
        "phoneme": "/ŋ/",
        "sound_type": "nasal",
        "voiced": True,
        "lips_label": "Nose Sound",
        "mouth_position": "Back of tongue touches soft palate, sound through nose",
        "hand_cue": "Point to back of throat then nose",
        "body_cue": "Like the end of 'sing' or 'ring'",
        "teaching_tip": "Back of tongue up, sound through nose. Singing sound!",
        "common_errors": ["Adding 'g' at end", "Making 'n' instead"],
        "feel_it": "Feel back of tongue up AND vibration in your nose",
        "visual_description": "Back of tongue raised, sound through nose",
        "throat_vibration": True,
        "nose_vibration": True,
    },

    # === LIQUIDS ===
    "l": {
        "phoneme": "/l/",
        "sound_type": "liquid",
        "voiced": True,
        "lips_label": "Tongue Tip Sound",
        "mouth_position": "Tongue tip on ridge behind teeth, air flows around sides of tongue",
        "hand_cue": "Lift hand up like tongue lifting",
        "body_cue": "Lift tongue tip up - 'la la la'",
        "teaching_tip": "Tongue tip UP to the spot behind your teeth. Singing sound!",
        "common_errors": ["Tongue tip too low", "Using back of tongue"],
        "feel_it": "Feel your tongue tip press up against the ridge and hold there",
        "visual_description": "Tongue tip raised to ridge, air flows around sides",
        "throat_vibration": True,
    },
    "r": {
        "phoneme": "/r/",
        "sound_type": "liquid",
        "voiced": True,
        "lips_label": "Tongue Back Sound",
        "mouth_position": "Tongue bunched up in back or curled back, lips slightly rounded",
        "hand_cue": "Curl fingers back or make growling gesture",
        "body_cue": "Growl like a lion or angry dog - 'rrrr'",
        "teaching_tip": "Tongue pulls back, lips round slightly. Growling sound!",
        "common_errors": ["Tongue touching roof of mouth", "Making 'w' sound"],
        "feel_it": "Feel your tongue bunch up in the back without touching anything",
        "visual_description": "Tongue curled or bunched back, lips slightly rounded",
        "throat_vibration": True,
    },

    # === GLIDES ===
    "w": {
        "phoneme": "/w/",
        "sound_type": "glide",
        "voiced": True,
        "lips_label": "Lip Rounder",
        "mouth_position": "Lips start rounded tight (like 'oo'), then open to next sound",
        "hand_cue": "Make 'O' with fingers, then open them",
        "body_cue": "Start with tight round lips like blowing a candle, then open",
        "teaching_tip": "Start with round lips like saying 'oo', then glide to next sound",
        "common_errors": ["Lips not round enough at start", "Not gliding to next sound"],
        "feel_it": "Feel your lips start tight and round, then relax open",
        "visual_description": "Lips tightly rounded then opening",
        "throat_vibration": True,
    },
    "y": {
        "phoneme": "/j/",
        "sound_type": "glide",
        "voiced": True,
        "lips_label": "Tongue Glider",
        "mouth_position": "Tongue high and front (like 'ee'), then glides to next sound",
        "hand_cue": "Hand moves from high position down",
        "body_cue": "Start with 'ee' mouth, glide to next sound",
        "teaching_tip": "Tongue starts high like saying 'ee', then moves to next sound",
        "common_errors": ["Tongue not high enough", "Adding extra sounds"],
        "feel_it": "Feel your tongue start high and front, then move down",
        "visual_description": "Tongue high and front, then gliding down",
        "throat_vibration": True,
    },

    # === AFFRICATES ===
    "ch": {
        "phoneme": "/tʃ/",
        "sound_type": "affricate",
        "voiced": False,
        "lips_label": "Tongue Tip + Fat Sound",
        "mouth_position": "Starts like /t/ then releases into /sh/",
        "hand_cue": "One finger starts touching palm, then slides forward",
        "body_cue": "Like a train - 'ch ch ch choo choo'",
        "teaching_tip": "It's /t/ + /sh/ together really fast. Train sound!",
        "common_errors": ["Making just 'sh'", "Making just 't'"],
        "feel_it": "Feel the /t/ stop, then the /sh/ air release right after",
        "visual_description": "Quick /t/ followed immediately by /sh/",
        "throat_vibration": False,
    },
    "j_sound": {
        "phoneme": "/dʒ/",
        "sound_type": "affricate",
        "voiced": True,
        "lips_label": "Tongue Tip + Fat Sound",
        "mouth_position": "Starts like /d/ then releases into /zh/, with voice",
        "hand_cue": "Two fingers start touching palm, then slide forward",
        "body_cue": "Like jumping - 'j j j jump!'",
        "teaching_tip": "It's /d/ + /zh/ together with voice. Jumping sound!",
        "common_errors": ["Making just 'zh'", "Not using voice"],
        "feel_it": "Feel the /d/ stop, then /zh/ release, AND throat vibrating",
        "visual_description": "Quick /d/ followed by voiced /zh/",
        "throat_vibration": True,
    },

    # === SPECIAL ===
    "ks": {
        "phoneme": "/ks/",
        "sound_type": "blend",
        "voiced": False,
        "lips_label": "Blend",
        "mouth_position": "Quick /k/ from back of throat followed by /s/ with teeth together",
        "hand_cue": "Back tap then snake motion",
        "body_cue": "Two sounds blended together - 'k' then 's' fast",
        "teaching_tip": "Say /k/ then /s/ really fast together. Usually at END of words (box, fox)!",
        "common_errors": ["Separating the sounds too much", "Adding vowel between"],
        "feel_it": "Feel back of tongue tap, then immediately thin air through teeth",
        "visual_description": "Back tongue tap, then teeth together for /s/",
        "throat_vibration": False,
    },
    "kw": {
        "phoneme": "/kw/",
        "sound_type": "blend",
        "voiced": False,
        "lips_label": "Blend",
        "mouth_position": "Quick /k/ from back of throat followed by rounded lips /w/",
        "hand_cue": "Back tap then round lips motion",
        "body_cue": "Make a /k/ then immediately round lips like /w/",
        "teaching_tip": "Q always has U with it! Say /k/ + /w/ fast together.",
        "common_errors": ["Forgetting the /w/ part", "Making 'kuh' instead"],
        "feel_it": "Feel back of tongue tap, then immediately lips round",
        "visual_description": "Back tongue tap, then lips round for /w/",
        "throat_vibration": False,
    },

    # === NUMBER WORDS ===
    "zero": {
        "phoneme": "/z/",
        "sound_type": "number",
        "voiced": True,
        "lips_label": "Number Word",
        "mouth_position": "Start with teeth together for /z/, then open for 'ee-ro'",
        "hand_cue": "Make a zero/circle with thumb and finger",
        "body_cue": "Buzz like a bee for the /z/ sound - 'zzzz-ee-ro'",
        "teaching_tip": "Starts with a buzzing Z sound. Zee-ro!",
        "common_errors": ["Saying 'see-ro'", "Forgetting the Z buzz"],
        "feel_it": "Feel the buzz in your throat when you start the Z",
        "visual_description": "Teeth together buzzing, then mouth opens",
        "throat_vibration": True,
    },
    "one": {
        "phoneme": "/w/",
        "sound_type": "number",
        "voiced": True,
        "lips_label": "Number Word",
        "mouth_position": "Start with rounded lips for /w/, open to 'uh', end with /n/",
        "hand_cue": "Hold up one finger",
        "body_cue": "Round your lips tight then open - 'wuh-n'",
        "teaching_tip": "Starts with rounded lips like W. Wuh-n!",
        "common_errors": ["Not rounding lips at start", "Saying 'won' like 'win'"],
        "feel_it": "Feel your lips start round and tight, then open",
        "visual_description": "Lips round then open, tongue taps for N",
        "throat_vibration": True,
    },
    "two": {
        "phoneme": "/t/",
        "sound_type": "number",
        "voiced": False,
        "lips_label": "Number Word",
        "mouth_position": "Tongue taps behind teeth for /t/, then lips round for 'oo'",
        "hand_cue": "Hold up two fingers (peace sign)",
        "body_cue": "Quick tongue tap then round lips - 't-oo'",
        "teaching_tip": "Quick T tap, then round lips for OO. Too!",
        "common_errors": ["Adding 'uh' after T", "Not rounding lips enough"],
        "feel_it": "Feel tongue tap, then lips push forward and round",
        "visual_description": "Tongue taps, then lips round forward",
        "throat_vibration": False,
    },
    "three": {
        "phoneme": "/θr/",
        "sound_type": "number",
        "voiced": False,
        "lips_label": "Number Word",
        "mouth_position": "Tongue between teeth for /th/, pull back for /r/, then 'ee'",
        "hand_cue": "Hold up three fingers",
        "body_cue": "Stick tongue out slightly, then pull it back - 'th-r-ee'",
        "teaching_tip": "Tongue peeks out for TH, then pulls back. Th-ree!",
        "common_errors": ["Saying 'free' or 'tree'", "Tongue not coming out for TH"],
        "feel_it": "Feel air flow over your tongue tip, then tongue pulls back",
        "visual_description": "Tongue tip visible, then retracts for R",
        "throat_vibration": False,
    },
    "four": {
        "phoneme": "/f/",
        "sound_type": "number",
        "voiced": False,
        "lips_label": "Number Word",
        "mouth_position": "Top teeth on lower lip for /f/, then open for 'or'",
        "hand_cue": "Hold up four fingers",
        "body_cue": "Teeth on lip, blow air - 'f-or'",
        "teaching_tip": "Teeth gently on lip, blow air. For!",
        "common_errors": ["Biting lip too hard", "Not enough air flow"],
        "feel_it": "Feel teeth touch lip and cool air flow out",
        "visual_description": "Upper teeth on lower lip, then mouth opens",
        "throat_vibration": False,
    },
    "five": {
        "phoneme": "/f/",
        "sound_type": "number",
        "voiced": False,
        "lips_label": "Number Word",
        "mouth_position": "Top teeth on lower lip for /f/, then 'eye-v'",
        "hand_cue": "Hold up five fingers (whole hand)",
        "body_cue": "Teeth on lip, blow, then open wide - 'f-eye-v'",
        "teaching_tip": "Starts AND ends with teeth-on-lip sounds! F...ive!",
        "common_errors": ["Missing the V at the end", "Not enough F at start"],
        "feel_it": "Feel teeth on lip twice - at start and end!",
        "visual_description": "Teeth on lip, mouth opens wide, teeth on lip again",
        "throat_vibration": False,
    },
    "six": {
        "phoneme": "/s/",
        "sound_type": "number",
        "voiced": False,
        "lips_label": "Number Word",
        "mouth_position": "Teeth together for /s/, open for 'ih', end with /ks/",
        "hand_cue": "Show six fingers (one hand plus one)",
        "body_cue": "Hiss like a snake, then 'icks' - 's-ih-ks'",
        "teaching_tip": "Snake sound at start, ends with X sound. Ssssix!",
        "common_errors": ["Saying 'sick' without the S", "Missing the KS at end"],
        "feel_it": "Feel thin air through teeth at start and end",
        "visual_description": "Teeth close for S, open, teeth close for KS",
        "throat_vibration": False,
    },
    "seven": {
        "phoneme": "/s/",
        "sound_type": "number",
        "voiced": False,
        "lips_label": "Number Word",
        "mouth_position": "Teeth together for /s/, then 'eh-vun'",
        "hand_cue": "Show seven fingers",
        "body_cue": "Snake sound, then 'eh-vun' - 's-eh-vun'",
        "teaching_tip": "Starts with snake S, has V in the middle. Seh-vun!",
        "common_errors": ["Saying 'sebben'", "Missing the V sound"],
        "feel_it": "Feel the S hiss, then teeth on lip for V",
        "visual_description": "Teeth together, open, teeth on lip for V",
        "throat_vibration": False,
    },
    "eight": {
        "phoneme": "/eɪ/",
        "sound_type": "number",
        "voiced": True,
        "lips_label": "Number Word",
        "mouth_position": "Open mouth for long A sound, end with tongue tap for /t/",
        "hand_cue": "Show eight fingers",
        "body_cue": "Say the letter A, then add T - 'ay-t'",
        "teaching_tip": "Sounds like the letter A plus T! Ay-t!",
        "common_errors": ["Adding 'uh' at start", "Forgetting the T at end"],
        "feel_it": "Feel mouth open for A, then tongue taps for T",
        "visual_description": "Mouth opens for A sound, tongue taps at end",
        "throat_vibration": True,
    },
    "nine": {
        "phoneme": "/n/",
        "sound_type": "number",
        "voiced": True,
        "lips_label": "Number Word",
        "mouth_position": "Tongue on ridge for /n/, open for 'eye', back to /n/",
        "hand_cue": "Show nine fingers",
        "body_cue": "Hum through nose, open, hum again - 'n-eye-n'",
        "teaching_tip": "Starts AND ends with tongue-on-ridge N! N-eye-n!",
        "common_errors": ["Missing one of the N sounds", "Saying 'mine'"],
        "feel_it": "Feel tongue touch ridge twice - nose hums at start and end",
        "visual_description": "Tongue up, mouth opens wide, tongue up again",
        "throat_vibration": True,
        "nose_vibration": True,
    },
}

# Map letters to their primary sound cue (for kindergarten, we use the most common sound)
LETTER_TO_SOUND = {
    # Vowels (short sounds)
    "A": "short_a", "a": "short_a",
    "E": "short_e", "e": "short_e",
    "I": "short_i", "i": "short_i",
    "O": "short_o", "o": "short_o",
    "U": "short_u", "u": "short_u",
    # Consonants
    "B": "b", "b": "b",
    "C": "k", "c": "k",  # Hard C (most common in kindergarten words)
    "D": "d", "d": "d",
    "F": "f", "f": "f",
    "G": "g", "g": "g",  # Hard G
    "H": "h", "h": "h",
    "J": "j_sound", "j": "j_sound",
    "K": "k", "k": "k",
    "L": "l", "l": "l",
    "M": "m", "m": "m",
    "N": "n", "n": "n",
    "P": "p", "p": "p",
    "Q": "kw", "q": "kw",
    "R": "r", "r": "r",
    "S": "s", "s": "s",
    "T": "t", "t": "t",
    "V": "v", "v": "v",
    "W": "w", "w": "w",
    "X": "ks", "x": "ks",
    "Y": "y", "y": "y",
    "Z": "z", "z": "z",
    # Numbers
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
}


def get_articulation_cue(character: str) -> Optional[dict]:
    """
    Get articulation cue data for a character.

    Args:
        character: A single letter (A-Z, a-z)

    Returns:
        Dictionary with articulation cue data, or None if not found
    """
    sound_key = LETTER_TO_SOUND.get(character)
    if sound_key:
        cue_data = SOUND_CUES.get(sound_key, {}).copy()
        cue_data["sound_key"] = sound_key
        return cue_data
    return None


def get_mouth_description(character: str) -> Optional[str]:
    """Get just the mouth position description for a character."""
    cue = get_articulation_cue(character)
    return cue.get("mouth_position") if cue else None


def get_hand_cue(character: str) -> Optional[str]:
    """Get just the hand cue description for a character."""
    cue = get_articulation_cue(character)
    return cue.get("hand_cue") if cue else None


def get_teaching_tip(character: str) -> Optional[str]:
    """Get the teaching tip for a character."""
    cue = get_articulation_cue(character)
    return cue.get("teaching_tip") if cue else None


def is_voiced(character: str) -> Optional[bool]:
    """Check if a character's sound is voiced (throat vibration)."""
    cue = get_articulation_cue(character)
    return cue.get("voiced") if cue else None


def get_lips_label(character: str) -> Optional[str]:
    """Get the LiPS-style descriptive label for a sound."""
    cue = get_articulation_cue(character)
    return cue.get("lips_label") if cue else None


# Image/animation support structure
ARTICULATION_MEDIA = {
    # This structure supports future addition of images/animations
    # Each sound can have multiple media types
    "short_a": {
        "mouth_image": None,  # Path to mouth position image
        "mouth_animation": None,  # Path to animated GIF/video
        "hand_cue_image": None,  # Path to hand gesture image
        "hand_cue_animation": None,
        "side_view_image": None,  # Side cross-section view
        "front_view_image": None,  # Front view of mouth
    },
    # ... same structure for all sounds
}


def get_articulation_media(character: str) -> Optional[dict]:
    """
    Get media paths for articulation cues.

    Returns dictionary with paths to images/animations for the character's sound.
    """
    sound_key = LETTER_TO_SOUND.get(character)
    if sound_key:
        return ARTICULATION_MEDIA.get(sound_key)
    return None


# For API endpoint support
def get_all_articulation_data() -> dict:
    """Get all articulation cue data for API response."""
    return {
        "sounds": SOUND_CUES,
        "letter_mapping": LETTER_TO_SOUND,
    }
