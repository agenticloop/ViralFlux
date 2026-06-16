"""Genre definitions for ViralFlux.

A genre drives: the script-writing style (Gemini prompt), the recommended
ElevenLabs voices + voice settings, the visual path (generated images vs CC0
loop footage), the music mood bucket, and the caption style preset.

New genres = a new entry here. No core pipeline changes required.
"""
from __future__ import annotations

# Visual path constants
VISUAL_GENERATED = "generated_images"   # Imagen scenes + ken-burns (horror)
VISUAL_LOOP = "loop_footage"            # CC0 satisfying loops (brainrot)

# ElevenLabs premade voices (verified/cached at boot via GET /v1/voices).
HORROR_VOICES = [
    {"name": "Bill", "voice_id": "pqHfZKP75CvOlQylNhV4", "desc": "Deep, commanding American male. Default horror narrator."},
    {"name": "Daniel", "voice_id": "onwK4e9ZLuTAKqWW03F9", "desc": "Deep British male. True-crime documentary feel."},
    {"name": "Callum", "voice_id": "N2lVS1w4EtoT3dr4eOWO", "desc": "Hoarse, intense male. Disturbing monologues."},
    {"name": "Fin", "voice_id": "D38z5RcWu1voky8WS1ja", "desc": "Old raspy male. Gritty and worn."},
    {"name": "Harry", "voice_id": "SOYHLrjzK2X1ezoPC6cr", "desc": "Warm but anxious male. First-person terror."},
    {"name": "Arnold", "voice_id": "VR6AewLTigWG4xSOukaG", "desc": "Crisp American narrator. 'Based on true events'."},
    {"name": "Clyde", "voice_id": "2EiwWnXFnvU5JabPnv8n", "desc": "Eerie undertone. Reliable suspense narration."},
    {"name": "Glinda", "voice_id": "z9fAnlkpzviPz146aGWa", "desc": "Dark female. Sinister, supernatural/witch horror."},
    {"name": "Thomas", "voice_id": "GBv7mTt0atIp3Br8iCZE", "desc": "Calm, deep American. Slow-burn psychological horror."},
]

BRAINROT_VOICES = [
    {"name": "Adam", "voice_id": "pNInz6obpgDQGcFmaJgB", "desc": "Deep, ironically serious. Overdramatic brainrot."},
    {"name": "Liam", "voice_id": "TX3LPaxmHKxFdv7VOQHJ", "desc": "Young, fast, expressive. Chaotic meme narration."},
    {"name": "Sam", "voice_id": "yoZ06aMxZJJ28mfd3POQ", "desc": "Raspy, low, deadpan delivery."},
    {"name": "Charlie", "voice_id": "IKne3meq5aSn9XLyUdCD", "desc": "Casual English. Unhinged British commentary."},
    {"name": "Antoni", "voice_id": "ErXwobaYiN019PkySvjV", "desc": "Natural, conversational brainrot."},
    {"name": "Ethan", "voice_id": "g5CIjZEefAph4nQFvHAz", "desc": "ASMR whisper. Crossover horror-brainrot."},
    {"name": "Patrick", "voice_id": "ODq5zmih8GrVes37Dx0d", "desc": "Composed American. Ironically calm narration."},
]

GENRES: dict[str, dict] = {
    "horror": {
        "slug": "horror",
        "name": "Horror",
        "description": "Atmospheric first-person/true-events horror narration.",
        "visual": VISUAL_GENERATED,
        "music_bucket": "horror_ambient",
        "caption_style": "horror",      # clean, slower fade
        "default_voice_id": "pqHfZKP75CvOlQylNhV4",  # Bill
        "voices": HORROR_VOICES,
        "voice_settings": {
            "stability": 0.35,
            "similarity_boost": 0.75,
            "style": 0.45,
            "use_speaker_boost": True,
        },
        "image_style_prefix": (
            "cinematic horror photography, dark atmospheric lighting, eerie, "
            "film grain, desaturated, foreboding, 9:16 vertical"
        ),
    },
    "brainrot": {
        "slug": "brainrot",
        "name": "Brainrot",
        "description": "Chaotic, deadpan, high-energy narration over satisfying loops.",
        "visual": VISUAL_LOOP,
        "music_bucket": "upbeat_hype",
        "caption_style": "brainrot",    # bold, energetic, heavy stroke
        "default_voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam
        "voices": BRAINROT_VOICES,
        "voice_settings": {
            "stability": 0.25,
            "similarity_boost": 0.70,
            "style": 0.65,
            "use_speaker_boost": True,
        },
        "image_style_prefix": "",  # uses loop footage, not generated images
    },
    "custom": {
        "slug": "custom",
        "name": "Custom",
        "description": "User-defined genre via seed prompt. Pro+ only.",
        "visual": VISUAL_GENERATED,
        "music_bucket": "cinematic_epic",
        "caption_style": "horror",
        "default_voice_id": "VR6AewLTigWG4xSOukaG",  # Arnold (neutral narrator)
        "voices": HORROR_VOICES + BRAINROT_VOICES,
        "voice_settings": {
            "stability": 0.40,
            "similarity_boost": 0.75,
            "style": 0.45,
            "use_speaker_boost": True,
        },
        "image_style_prefix": "cinematic, high detail, 9:16 vertical",
    },
}

GENRE_SLUGS = tuple(GENRES.keys())


def get_genre(slug: str) -> dict:
    return GENRES.get(slug, GENRES["horror"])


def voice_settings_for(slug: str) -> dict:
    return get_genre(slug)["voice_settings"]
