#!/usr/bin/env python3
"""
Generate Topic Video V7.4 (V7.3 + Styles + Top-Left Start)
1. Generate Beat Manifest with PARTS.
2. Generate Image (Fal.ai).
3. Generate Audio per-part.
4. Generate Video using DoodleVideoGeneratorV7_4 (Styles: Solid, Normal, Pencil).
"""



import os
import sys
import json
import argparse
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from create_doodle_video_v7_4 import DoodleVideoGeneratorV7_4

# --- CONFIGURATION ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
FAL_KEY = os.environ.get("FAL_KEY")
ELEVEN_LABS_KEY = os.environ.get("ELEVEN_LABS_API_KEY")

GROK_MODEL = "x-ai/grok-4.1-fast"
DEFAULT_ELEVEN_MODEL = "eleven_turbo_v2"  # Fast English model
# Use eleven_multilingual_v2 for non-English languages

def fetch_elevenlabs_voices():
    """
    Fetch all available voices from your ElevenLabs account.
    Returns a dict mapping voice_name (lowercase) -> voice_id
    """
    if not ELEVEN_LABS_KEY:
        return {}
    
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {"xi-api-key": ELEVEN_LABS_KEY}
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        voices = {}
        for voice in data.get("voices", []):
            name = voice.get("name", "").lower()
            voice_id = voice.get("voice_id")
            if name and voice_id:
                voices[name] = voice_id
        return voices
    except Exception as e:
        print(f"[TopicVideoV7.4] ⚠️ Could not fetch voices: {e}")
        return {}

# Cache for fetched voices (populated on demand)
_VOICES_CACHE = None

def get_voices():
    """Get voices (fetches once and caches)"""
    global _VOICES_CACHE
    if _VOICES_CACHE is None:
        _VOICES_CACHE = fetch_elevenlabs_voices()
    return _VOICES_CACHE

def get_voice_id(voice_name_or_id):
    """
    Resolve a voice name to its ID. 
    If it looks like an ID (long string), return as-is.
    Otherwise look up by name.
    """
    if not voice_name_or_id:
        # Return first available voice or None
        voices = get_voices()
        if voices:
            return list(voices.values())[0]
        return None
    
    # If it's already an ID (20+ chars), use directly
    if len(voice_name_or_id) > 15:
        return voice_name_or_id
    
    # Look up by name
    voices = get_voices()
    return voices.get(voice_name_or_id.lower(), voice_name_or_id)

def log(msg):
    print(f"[TopicVideoV7.4] {msg}", flush=True)

def ensure_keys():
    if not all([OPENROUTER_API_KEY, FAL_KEY, ELEVEN_LABS_KEY]):
        log("❌ Missing API Keys (OpenRouter, Fal, or ElevenLabs)")
        sys.exit(1)

# --- 1. MANIFEST WITH PARTS ---

def generate_beat_manifest(topic, language=None):
    """
    Generate beat manifest for the video.
    Args:
        topic: The topic for the video
        language: ISO 639-1 language code (e.g., 'hi' for Hindi, 'es' for Spanish)
    """
    log(f"🧠 Generating V7.4 Manifest (with parts) for: {topic}...")
    
    # Language instruction
    language_instruction = ""
    if language and language.lower() not in ['en', 'en-us', 'en-gb']:
        lang_map = {
            'hi': 'Hindi (हिन्दी)',
            'es': 'Spanish (Español)', 
            'de': 'German (Deutsch)',
            'fr': 'French (Français)',
            'ja': 'Japanese (日本語)',
            'zh': 'Chinese (中文)',
            'ko': 'Korean (한국어)',
            'pt': 'Portuguese (Português)',
            'it': 'Italian (Italiano)',
            'ar': 'Arabic (العربية)',
            'ru': 'Russian (Русский)',
        }
        lang_name = lang_map.get(language.lower(), language)
        language_instruction = f"""
    ### CRITICAL: LANGUAGE
    Write ALL "audio_script" text primarily in {lang_name}, BUT keep key technical terms, 
    scientific words, and important jargon in English. This hybrid approach (like Hinglish) 
    helps users understand complex concepts better.
    
    Example for Hindi: "Einstein ki Theory of Relativity kehti hai ki space aur time ek saath 
    connected hain, jise hum spacetime kehte hain."
    
    Keep "image_prompt" and "visual_desc" in English (for image generation).
    """
        log(f"   📝 Script language: {lang_name}")
    
    prompt = f"""
    You are a whiteboard video script expert.
    Create a video script for: "{topic}".
    {language_instruction}
    ### CRITICAL: STRUCTURE WITH PARTS
    Each beat MUST have a "parts" array. Parts are visual sections of the diagram.
    
    ### FLEXIBLE SEGMENTATION (SMART LAYOUT)
    Choose 1, 2, or 3 parts based on content:
    
    [1 PART] Single concept, one main idea, or complex unified diagram.
    [2 PARTS] Comparisons (A vs B), before/after, cause/effect.
    [3 PARTS] Step-by-step flows, processes, sequences.
    
    ### PARTS STRUCTURE
    - "position": 0=Left, 1=Center, 2=Right
    - "audio_script": 1-2 sentences explaining THIS part
    - "visual_desc": What's drawn in this section
    
    ### OUTPUT (JSON ONLY)
    {{
      "topic": "{topic}",
      "beats": [
        {{ 
          "beat_id": 1,
          "image_prompt": "...",
          "parts": [
            {{"position": 0, "visual_desc": "...", "audio_script": "..."}},
            ...
          ]
        }}
      ]
    }}
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://learning-software.local",
    }
    
    payload = {
        "model": GROK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }

    try:
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        content = resp.json()['choices'][0]['message']['content']
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        return json.loads(content)
    except Exception as e:
        log(f"❌ Manifest Error: {e}")
        return None

# --- 2. ASSETS ---

def generate_image_fal(prompt, output_path, style="normal"):
    # Styles:
    # solid -> Vivid Color, Markers (Clean)
    # normal -> Black Ink Sketch (Marker texture)
    # pencil -> Pencil Sketch (Graphite texture)
    
    if style == "pencil":
        style_suffix = ", detailed graphite pencil sketch on white paper, gray lines, hand-drawn, artistic, shading, technical drawing style"
        negative_prompt = "color, ink, marker, heavy lines, solid black, photo, realistic, 3d, digital art"
        
    elif style == "normal" or style == "sketch": # Backwards compat
        style_suffix = ", classic whiteboard diagram, black ink sketch on pure white background, minimal clean lines, simple icons, clear text labels, hand-drawn style, high contrast, educational, natural flow"
        negative_prompt = "color, colored, complex, filled, gradients, photo, realistic, dark background, blue background, blurry, vertical lines, divider lines, section borders, grid lines"
        
    else: # solid / color (Now "Infographic")
        style_suffix = ", colorful infographic on pure white background, fine colored lines, technical diagram, elegant, clean, no heavy fills, vibrant colors, educational, vector style"
        negative_prompt = "grayscale, black and white, monochrome, dark background, texture, heavy fills, painting, realistic, photo, 3d, gradient, blurry, messy, sketch, pencil"
        
    full_prompt = prompt + style_suffix
    
    log(f"🎨 Generating Image ({style}): {prompt[:40]}...")
    url = "https://fal.run/fal-ai/nano-banana" 
    headers = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}
    payload = {
        "prompt": full_prompt,
        "negative_prompt": negative_prompt,
        "aspect_ratio": "16:9",
        "num_inference_steps": 8,
        "enable_safety_checker": False
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        if 'images' in result and len(result['images']) > 0:
            img_url = result['images'][0]['url']
            with open(output_path, "wb") as f:
                f.write(requests.get(img_url).content)
            return True
        return False
    except Exception as e:
        log(f"❌ Fal Error: {e}")
        return False

def generate_audio_part(text, output_path, voice=None, language_code=None):
    """
    Generate audio using ElevenLabs TTS API.
    
    Args:
        text: Text to convert to speech
        output_path: Path to save the audio file
        voice: Voice name (from your ElevenLabs account) or voice ID
        language_code: ISO 639-1 language code (e.g., 'en', 'es', 'de', 'fr', 'ja', 'zh', 'hi')
                      When set, uses eleven_multilingual_v2 model for better language support
    """
    # Resolve voice name to ID (fetches from your account)
    voice_id = get_voice_id(voice)
    if not voice_id:
        log("❌ No voice available. Check your ElevenLabs API key.")
        return False
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": ELEVEN_LABS_KEY, "Content-Type": "application/json"}
    
    # Use multilingual model when language is specified (except English)
    if language_code and language_code.lower() not in ['en', 'en-us', 'en-gb']:
        model_id = "eleven_multilingual_v2"
    else:
        model_id = DEFAULT_ELEVEN_MODEL
    
    payload = {
        "text": text, 
        "model_id": model_id, 
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    
    # Add language_code if specified (helps with pronunciation)
    if language_code:
        payload["language_code"] = language_code
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(resp.content)
        return True
    except Exception as e:
        log(f"❌ Audio Error: {e}")
        return False

# --- MAIN ---

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", help="Topic")
    parser.add_argument("--output_dir", default="topic_videos_v7_4", help="Output dir")
    parser.add_argument("--max_beats", type=int, default=0)
    # Styles: 'normal' (Sketch/Ink), 'solid' (Color/Marker), 'pencil' (Graphite)
    parser.add_argument("--style", default="normal", choices=["normal", "solid", "pencil"], help="Image/Doodle style")
    # Voice options
    parser.add_argument("--voice", default=None, 
        help="Voice name (from your ElevenLabs account) or voice ID. Use --list_voices to see available.")
    parser.add_argument("--language", default=None, 
        help="ISO 639-1 language code (e.g., 'en', 'es', 'de', 'fr', 'ja', 'zh', 'hi'). Uses multilingual model for non-English.")
    parser.add_argument("--list_voices", action="store_true", help="List all available voices from your ElevenLabs account")
    args = parser.parse_args()

    # Handle --list_voices - fetch from API
    if args.list_voices:
        print("\n🎙️  Fetching voices from your ElevenLabs account...")
        voices = get_voices()
        if not voices:
            print("❌ Could not fetch voices. Check your ELEVEN_LABS_API_KEY.")
            sys.exit(1)
        print(f"\n✅ Found {len(voices)} voices:\n")
        for name, voice_id in sorted(voices.items()):
            print(f"    • {name} ({voice_id[:8]}...)")
        print(f"\n  Usage: --voice \"voice name here\"")
        print(f"  Example: --voice \"{list(voices.keys())[0]}\"")
        sys.exit(0)

    ensure_keys()
    
    safe_topic = args.topic.lower().replace(" ", "_")
    work_dir = os.path.join(args.output_dir, safe_topic)
    os.makedirs(work_dir, exist_ok=True)
    
    manifest = generate_beat_manifest(args.topic, language=args.language)
    if not manifest: return
    
    beats = manifest.get("beats", [])
    if args.max_beats > 0: beats = beats[:args.max_beats]
    
    final_clips = []
    
    for i, beat in enumerate(beats):
        beat_id = i + 1
        log(f"\n--- Beat {beat_id} ---")
        
        base_name = f"beat_{beat_id}"
        image_path = os.path.join(work_dir, f"{base_name}.png")
        final_beat_path = os.path.join(work_dir, f"{base_name}_doodle.mp4")
        
        # A. Image
        if not os.path.exists(image_path):
            if not generate_image_fal(beat["image_prompt"], image_path, style=args.style): 
                continue

        # B. Get parts
        parts = beat.get("parts", [])
        if not parts:
            narrator_script = beat.get("narrator_script", "")
            if narrator_script:
                parts = [{"position": 0, "audio_script": narrator_script, "visual_desc": "full"}]
            else:
                log("❌ No parts/script. Skipping.")
                continue
        
        # C. Generate Audio & Segments
        audio_clips = []
        segments = []
        
        for p_idx, part in enumerate(parts):
            p_audio_path = os.path.join(work_dir, f"{base_name}_part_{p_idx}.mp3")
            p_script = part.get("audio_script", "")
            p_position = part.get("position", p_idx)
            
            if not p_script: continue
            
            if not os.path.exists(p_audio_path):
                generate_audio_part(p_script, p_audio_path, voice=args.voice, language_code=args.language)
            
            try:
                ac = AudioFileClip(p_audio_path)
                # Trim silence/add pause
                audio_clips.append(ac)
                segments.append({
                    "position": p_position,
                    "duration": ac.duration + 0.3 # Tiny pause
                })
                log(f"   🎙️ Part {p_idx} (pos={p_position}): {ac.duration:.1f}s")
            except Exception as e:
                log(f"   ⚠️ Audio read error: {e}")
        
        if not audio_clips: continue
        
        # D. Combine Audio
        full_audio = concatenate_audioclips(audio_clips)
        total_duration = full_audio.duration + 1.0 # End hold
        
        log(f"   📊 {len(segments)} segments, total duration: {total_duration:.1f}s")
        
        # E. Generate Doodle (V7.4)
        if not os.path.exists(final_beat_path):
            try:
                # Pass 'style' to generator
                gen = DoodleVideoGeneratorV7_4(
                    image_path, 
                    final_beat_path, 
                    segments=segments,
                    duration=total_duration,
                    style=args.style
                )
                gen.generate()
            except Exception as e:
                log(f"❌ Doodle Error: {e}")
                continue
        
        # F. Mux
        try:
            video_clip = VideoFileClip(final_beat_path)
            video_clip = video_clip.set_audio(full_audio)
            final_clips.append(video_clip)
            log(f"   ✅ Beat {beat_id} ready.")
        except Exception as e:
            log(f"❌ Mux Error: {e}")
            
    # Final Stitch
    if final_clips:
        log("\n🎞️ Stitching...")
        out_path = os.path.join(work_dir, f"video_v7_4_{safe_topic}_{args.style}.mp4")
        concatenate_videoclips(final_clips).write_videofile(out_path, codec="libx264", audio_codec="aac")
        log(f"🎉 Done: {out_path}")
    else:
        log("❌ No clips.")

if __name__ == "__main__":
    main()
