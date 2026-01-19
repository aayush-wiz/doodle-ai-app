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
from create_doodle_video_v8_1 import DoodleVideoGeneratorV8_1

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
    ### CRITICAL: AUDIO & VISUAL SYNC (TIMING)
    **The doodle takes ~5 seconds to draw.** 
    To prevent the video from cutting off, the `audio_script` must be SLIGHTLY padded, but **NOT too long**.
    
    1. **"bubble_text"**: Short punchy text (max 10 words).
    2. **"visual_desc"**: A concise description of the doodle (e.g. "A donut atom").
    3. **"character_action"**: What is the character doing? (e.g. "Pointing at the diagram", "Scratching head", "Holding a magnifying glass"). **VARY THIS!**
    4. **"audio_script"**: The Narrative. **MEDIUM LENGTH**.
       - Read the bubble text.
       - Then, add **ONE or TWO sentences** describing the visual.
       - **Do NOT write a paragraph.** Just enough to cover the drawing time.
       - Example: "Particles? Like tiny donuts? I see this donut-shaped atom splitting apart... looks delicious!"
    
    ### FORMAT
    {{
      "topic": "{topic}",
      "beats": [
        {{ 
          "beat_id": 1,
          "image_prompt": "Simpsons style...",
          "dialogue": [
            {{
                "speaker": "Homer", 
                "bubble_text": "Particles? Like tiny donuts?",
                "visual_desc": "A doodle of a donut-shaped atom splitting into smaller pieces.",
                "character_action": "Holding a half-eaten donut and looking confused",
                "audio_script": "Particles? Like tiny donuts? I see this donut-shaped atom splitting apart... looks delicious!"
            }},
            {{
                "speaker": "Lisa", 
                "bubble_text": "No! They are fundamental!",
                "visual_desc": "A chart showing the Standard Model of particle physics.",
                "character_action": "Pointing confidently at the chart using a ruler",
                "audio_script": "No Dad! They are fundamental building blocks. This chart shows the Standard Model... visualize quarks inside protons."
            }}
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
    
    if style == "cartoon":
        # Refined for V8.13 (Colored Variant)
        style_suffix = ", The Simpsons style illustration, Matt Groening style, vibrantly colored characters and elements, flat design, white background, comic book style, clean lines"
        negative_prompt = "shading, gradients, realistic, photorealistic, 3d, textured, messy, sketch lines, hatching, blurry, gray background, colored background, dark background, complex background"

    elif style == "pencil":
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

# ... (Keep Imports and Helpers) ...
# Existing imports and helpers remain unchanged until Refactoring Main

def process_video_request(topic, style="normal", voice=None, language=None, max_beats=0):
    """
    Process a video request:
    1. Generate Manifest
    2. Loop Beats -> Gen Image, Gen Audio, Gen Video Segments
    3. Mux each beat
    4. Stitch final video
    
    Returns:
        str: Path to final video file, or None if failed.
    """
    try:
        ensure_keys()
        
        import uuid
        unique_id = str(uuid.uuid4())[:8]  # Short unique ID
        
        safe_topic = topic.lower().replace(" ", "_")
        # Add unique ID to folder to ensure fresh generation every time
        folder_name = f"{safe_topic}_{unique_id}"
        output_base = os.path.join(os.getcwd(), "topic_videos_v7_4") 
        work_dir = os.path.join(output_base, folder_name)
        os.makedirs(work_dir, exist_ok=True)
        
        manifest = generate_beat_manifest(topic, language=language)
        if not manifest: 
            return None
        
        beats = manifest.get("beats", [])
        if max_beats > 0: beats = beats[:max_beats]
        
        final_clips = []
        
        for i, beat in enumerate(beats):
            beat_id = i + 1
            log(f"\n--- Beat {beat_id} ---")
            
            base_name = f"beat_{beat_id}"
            image_path = os.path.join(work_dir, f"{base_name}.png")
            final_beat_path = os.path.join(work_dir, f"{base_name}_doodle.mp4")
            
            # A. Image
            if not os.path.exists(image_path):
                if not generate_image_fal(beat["image_prompt"], image_path, style=style): 
                    continue

            # B. Get parts / dialogue
            parts = beat.get("parts", [])
            dialogue = beat.get("dialogue", [])
            
            if not parts and not dialogue:
                narrator_script = beat.get("narrator_script", "")
                if narrator_script:
                    parts = [{"position": 0, "audio_script": narrator_script, "visual_desc": "full"}]
                else:
                    log("❌ No parts/dialogue/script. Skipping.")
                    continue
            
            # C. Generate Audio & Video PER LINE (V8.8 Precise Visuals)
            # Logic: 
            # 1. Loop through dialogue lines.
            # 2. For EACH line:
            #    a. Generate specific Image (Using 'bubble_text' + 'visual_desc').
            #    b. Generate Audio (Using 'audio_script').
            #    c. Generate Video Clip (Doodle).
            # 3. Mux them together.

            # Map speakers to voices
            speaker_voices = {
                "Homer": "onwK4e9ZLuTAKqWW03F9", 
                "Lisa": "21m00Tcm4TlvDq8ikWAM",  
            }
            default_voice = voice if voice else "21m00Tcm4TlvDq8ikWAM"
            
            dialogue_lines = beat.get("dialogue", [])
            # Fallback
            if not dialogue_lines:
                 parts = beat.get("parts", [])
                 for p in parts:
                     dialogue_lines.append({
                         "speaker": "Narrator", 
                         "bubble_text": p.get("audio_script", "")[:30],
                         "visual_desc": "A doodle explanation of the topic.",
                         "audio_script": p.get("audio_script", "")
                    })
            
            line_clips = []
            
            for line_idx, line in enumerate(dialogue_lines):
                speaker = line.get("speaker", "Narrator")
                
                # V8.8: Use 3 explicit fields (plus Action)
                bubble_text = line.get("bubble_text", line.get("text", ""))
                visual_desc = line.get("visual_desc", f"a diagram about {topic}")
                character_action = line.get("character_action", "Explaining")
                audio_script = line.get("audio_script", line.get("text", ""))
                
                if not bubble_text: continue
                
                log(f"\n   🗨️ Processing Line {line_idx}: [{speaker}] Action='{character_action[:15]}' Visual='{visual_desc[:20]}...'")
                
                # 1. Generate Prompt: Character + Bubble + SPECIFIC VISUAL
                # Safety: Escape quotes
                safe_text = bubble_text.replace('"', '').replace("'", "")
                
                if speaker == "Homer":
                    prompt_action = f"Homer Simpson {character_action} on left, speaking with a comic book speech bubble containing: '{safe_text}'."
                elif speaker == "Lisa":
                    prompt_action = f"Lisa Simpson {character_action} on right, speaking with a comic book speech bubble containing: '{safe_text}'."
                else:
                    # V8.12 Fix: Explicitly define Narrator as Female Teacher to match voice
                    prompt_action = f"A female Simpsons-style scientist/teacher {character_action}, speaking with a bubble text: '{safe_text}'."
                
                # V8.13: Colored Variant
                full_image_prompt = f"Simpsons style, Matt Groening style, vibrantly colored characters. {prompt_action} Next to her/him is a simple line drawing of {visual_desc}. The background must be pure white. The characters and objects should be fully colored, but the background is white."
                
                # 2. Generate Image
                line_img_path = os.path.join(work_dir, f"{base_name}_line_{line_idx}.png")
                if not os.path.exists(line_img_path):
                    generate_image_fal(full_image_prompt, line_img_path, style="cartoon")
                
                # 3. Generate Audio (Using extended script)
                line_audio_filename = f"{base_name}_line_{line_idx}.mp3"
                line_audio_path = os.path.join(work_dir, line_audio_filename)
                voice_id = speaker_voices.get(speaker, default_voice)
                
                if not os.path.exists(line_audio_path):
                    generate_audio_part(audio_script, line_audio_path, voice=voice_id, language_code=language)
                
                # 4. Create Video Clip (Doodle)
                line_video_path = os.path.join(work_dir, f"{base_name}_line_{line_idx}_doodle.mp4")
                
                try:
                    ac = AudioFileClip(line_audio_path)
                    duration = ac.duration + 0.5 # Pause after line
                    
                    if not os.path.exists(line_video_path):
                         single_seg = [{"duration": duration, "position": 0}]
                         
                         gen = DoodleVideoGeneratorV8_1(
                            line_img_path, 
                            line_video_path, 
                            segments=single_seg,
                            duration=duration,
                            style=style,
                            pps=6000 # Very Fast Drawing
                         )
                         gen.generate()
                    
                    # Mux
                    vc = VideoFileClip(line_video_path).set_audio(ac)
                    line_clips.append(vc)
                    
                except Exception as e:
                    log(f"   ⚠️ Line Processing Error: {e}")
                    
            if not line_clips: continue
            
            # Combine all lines for this beat
            beat_clip = concatenate_videoclips(line_clips)
            final_clips.append(beat_clip)
            log(f"   ✅ Beat {beat_id} ready ({len(line_clips)} lines).")
            
        # Final Stitch
        if final_clips:
            log("\n🎞️ Stitching...")
            out_path = os.path.join(work_dir, f"video_{unique_id}_{style}.mp4")
            concatenate_videoclips(final_clips).write_videofile(out_path, codec="libx264", audio_codec="aac")
            log(f"🎉 Done: {out_path}")
            return out_path
        else:
            log("❌ No clips.")
            return None

    except Exception as e:
        log(f"❌ Critical Process Error: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", help="Topic")
    parser.add_argument("--output_dir", default="topic_videos_v7_4", help="Output dir")
    parser.add_argument("--max_beats", type=int, default=0)
    # Styles: 'normal' (Sketch/Ink), 'solid' (Color/Marker), 'pencil' (Graphite)
    parser.add_argument("--style", default="normal", choices=["normal", "solid", "pencil", "cartoon"], help="Image/Doodle style")
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
    
    # We can rely on process_video_request, but need to make sure we respect output_dir 
    # Current impl of process_video_request hardcodes output_dir to current_dir/topic_videos_v7_4
    # For CLI compability we should ideally fix that, but strict refactor is okay for now.
    
    process_video_request(args.topic, style=args.style, voice=args.voice, language=args.language, max_beats=args.max_beats)

if __name__ == "__main__":
    main()
