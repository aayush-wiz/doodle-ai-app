"""
Lightweight ElevenLabs voice fetcher - no heavy dependencies.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ELEVEN_LABS_KEY = os.environ.get("ELEVEN_LABS_API_KEY")

_VOICES_CACHE = None

def fetch_elevenlabs_voices():
    """Fetch all available voices from ElevenLabs account."""
    if not ELEVEN_LABS_KEY:
        print("[Voices] Warning: ELEVEN_LABS_API_KEY not set")
        return {}
    
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {"xi-api-key": ELEVEN_LABS_KEY}
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        voices = {}
        for voice in data.get("voices", []):
            name = voice.get("name", "")
            voice_id = voice.get("voice_id")
            if name and voice_id:
                voices[name] = voice_id
        return voices
    except Exception as e:
        print(f"[Voices] Error fetching voices: {e}")
        return {}

def get_voices():
    """Get voices (fetches once and caches)"""
    global _VOICES_CACHE
    if _VOICES_CACHE is None:
        _VOICES_CACHE = fetch_elevenlabs_voices()
    return _VOICES_CACHE
