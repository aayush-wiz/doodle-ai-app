#!/usr/bin/env python3
"""
Generate Topic Video - Industrial Corporate Training Version
Based on V7.4 SOTA Logic.
Specialized for: Industrial Corporate Training Modules (Safety Icon Style).
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
from create_doodle_video_industrial import DoodleVideoGeneratorV7_4

# --- CONFIGURATION ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
FAL_KEY = os.environ.get("FAL_KEY")
ELEVEN_LABS_KEY = os.environ.get("ELEVEN_LABS_API_KEY")

GROK_MODEL = "x-ai/grok-4.1-fast"
DEFAULT_ELEVEN_MODEL = "eleven_turbo_v2" 

def fetch_elevenlabs_voices():
    if not ELEVEN_LABS_KEY: return {}
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
        print(f"[IndustrialVideo] ⚠️ Could not fetch voices: {e}")
        return {}

_VOICES_CACHE = None
def get_voices():
    global _VOICES_CACHE
    if _VOICES_CACHE is None: _VOICES_CACHE = fetch_elevenlabs_voices()
    return _VOICES_CACHE

def get_voice_id(voice_name_or_id):
    if not voice_name_or_id:
        voices = get_voices()
        return list(voices.values())[0] if voices else None
    if len(voice_name_or_id) > 15: return voice_name_or_id
    voices = get_voices()
    return voices.get(voice_name_or_id.lower(), voice_name_or_id)

def log(msg): print(f"[IndustrialVideo] {msg}", flush=True)

def ensure_keys():
    if not all([OPENROUTER_API_KEY, FAL_KEY, ELEVEN_LABS_KEY]):
        log("❌ Missing API Keys (OpenRouter, Fal, or ElevenLabs)")
        sys.exit(1)

# --- 1. MANIFEST WITH PARTS ---

def generate_beat_manifest(topic, language=None):
    log(f"🧠 Generating Industrial Corporate Training Manifest for: {topic}...")
    
    language_instruction = ""
    if language and language.lower() not in ['en', 'en-us', 'en-gb']:
        lang_map = {'hi': 'Hindi', 'es': 'Spanish', 'fr': 'French', 'de': 'German'} 
        lang_name = lang_map.get(language.lower(), language)
        language_instruction = f"""
        ### LANGUAGE: {lang_name}
        Write audio_script in {lang_name}. Keep technical terms in English.
        """
    
    # --- REFINED PROMPT: COMPREHENSIVE INDUSTRIAL TRAINING (MULTI-STYLE) ---
    prompt = f"""
    You are an EXPERT INSTRUCTIONAL DESIGNER for Industrial & Corporate Training.
    Create a COMPREHENSIVE VIDEO SCRIPT for: "{topic}"
    {language_instruction}
    
    ### VISUAL STYLE: ADAPTIVE INDUSTRIAL VECTOR
    The output must adapt to the content type. Choose the BEST layout for each beat:
    
    1. **SCENARIO (Workplace)**:
       - Use for: General intro, office rules, soft skills.
       - Visual: "Flat vector scene of [Worker/Office] in [Setting]. Blue/Grey palette."
       
    2. **SCHEMATIC (Equipment/Parts)**:
       - Use for: Machine parts, tools, technical specs.
       - Visual: "Technical line art diagram of [Machine], exploded view, minimal blue highlights, white background."
       
    3. **FLOWCHART (Process/Steps)**:
       - Use for: Procedures, sequences, "If This Then That".
       - Visual: "Industrial flowchart with arrows connecting [Icon A] -> [Icon B]. Blue/Yellow palette."
       
    4. **ICONOGRAPHY (Safety/Rules)**:
       - Use for: PPE, Do's/Don'ts, Checklists.
       - Visual: "Grid of 3 Safety Icons (Hard Hat, Boots, Vest), flat vector style, white background."
    
    ### CRITICAL: STRUCTURE (BEAT TYPES)
    
    **BEAT 1: INTRO TITLE CARD**
    - **Visual**: "Title Slide: '{topic}' text centered, with a relevant [Icon/Machine] illustration."
    - **Parts**: 1 Part.
    
    **BEAT 2+: TRAINING CONTENT (MULTI-PART)**
    - **MUST HAVE**: 2-3 distinct visual elements (Parts) to explain the concept.
    
    ### JSON OUTPUT FORMAT
    {{
      "topic": "{topic}",
      "beats": [
        {{ 
          "beat_id": 1,
          "image_prompt": "Industrial vector Title Card: '{topic}', workplace background scene, professional style, white background", 
          "parts": [
            {{ "position": 1, "visual_desc": "Intro Title", "audio_script": "Welcome to the module on {topic}." }}
          ]
        }},
        {{
          "beat_id": 2,
          "image_prompt": "Technical line art diagram of a Centrifugal Pump, exploded view, blue highlights. White background.",
          "parts": [
            {{ "position": 0, "visual_desc": "Impeller", "audio_script": "The impeller rotates to move fluid..." }},
            {{ "position": 1, "visual_desc": "Casing", "audio_script": "The casing directs the flow..." }}
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

def generate_image_fal(prompt, output_path, style="solid"):
    # --- REFINED STYLE: ADAPTIVE INDUSTRIAL VECTOR ---
    
    style_suffix = ", industrial vector illustration, flat style, professional corporate training, blue and yellow color palette, white background, clean lines, high quality, vector graphics, minimalist, no gradients, no photorealism"
    negative_prompt = "photo, realistic, 3d, textured, shading, gradients, messy, complex, artistic, painting, colorful, vibrant, dark background, gray background, chaotic"
        
    full_prompt = prompt + style_suffix
    
    log(f"🎨 Generating Image (Safety Icons): {prompt[:40]}...")
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
    voice_id = get_voice_id(voice)
    if not voice_id:
        log("❌ No voice available.")
        return False
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": ELEVEN_LABS_KEY, "Content-Type": "application/json"}
    
    if language_code and language_code.lower() not in ['en', 'en-us', 'en-gb']:
        model_id = "eleven_multilingual_v2"
    else:
        model_id = DEFAULT_ELEVEN_MODEL
    
    payload = {
        "text": text, 
        "model_id": model_id, 
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    if language_code: payload["language_code"] = language_code
    
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

def process_video_request(topic, style="solid", voice=None, language=None, max_beats=0):
    try:
        ensure_keys()
        
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        safe_topic = topic.lower().replace(" ", "_")
        folder_name = f"{safe_topic}_{unique_id}_industrial"
        output_base = os.path.join(os.getcwd(), "topic_videos_industrial") 
        work_dir = os.path.join(output_base, folder_name)
        os.makedirs(work_dir, exist_ok=True)
        
        manifest = generate_beat_manifest(topic, language=language)
        if not manifest: return None
        
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
                if not generate_image_fal(beat["image_prompt"], image_path, style="solid"): 
                    continue

            # B. Get parts
            parts = beat.get("parts", [])
            
            # C. Generate Audio & Segments
            audio_clips = []
            segments = []
            
            for p_idx, part in enumerate(parts):
                p_audio_path = os.path.join(work_dir, f"{base_name}_part_{p_idx}.mp3")
                p_script = part.get("audio_script", "")
                p_position = part.get("position", p_idx)
                
                if not p_script: continue
                
                if not os.path.exists(p_audio_path):
                    generate_audio_part(p_script, p_audio_path, voice=voice, language_code=language)
                
                try:
                    ac = AudioFileClip(p_audio_path)
                    audio_clips.append(ac)
                    segments.append({
                        "position": p_position,
                        "duration": ac.duration + 0.3
                    })
                    log(f"   🎙️ Part {p_idx}: {ac.duration:.1f}s")
                except Exception as e:
                    log(f"   ⚠️ Audio Error: {e}")
            
            if not audio_clips: continue
            
            # D. Combine Audio
            full_audio = concatenate_audioclips(audio_clips)
            total_duration = full_audio.duration + 1.0
            
            # E. Generate Doodle
            if not os.path.exists(final_beat_path):
                try:
                    gen = DoodleVideoGeneratorV7_4(
                        image_path, 
                        final_beat_path, 
                        segments=segments,
                        duration=total_duration,
                        style="solid"
                    )
                    gen.generate()
                except Exception as e:
                    log(f"❌ Doodle Error: {e}")
                    continue
            
            # F. Mux
            try:
                vc = VideoFileClip(final_beat_path).set_audio(full_audio)
                final_clips.append(vc)
                log(f"   ✅ Beat {beat_id} ready.")
            except Exception as e:
                log(f"❌ Mux Error: {e}")
                
        # Final Stitch
        if final_clips:
            log("\n🎞️ Stitching...")
            out_path = os.path.join(work_dir, f"video_{unique_id}.mp4")
            concatenate_videoclips(final_clips).write_videofile(out_path, codec="libx264", audio_codec="aac")
            log(f"🎉 Done: {out_path}")
            return out_path
        else:
            log("❌ No clips.")
            return None

    except Exception as e:
        log(f"❌ Process Error: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", help="Topic")
    parser.add_argument("--output_dir", default="topic_videos_industrial", help="Output dir")
    parser.add_argument("--max_beats", type=int, default=0)
    parser.add_argument("--style", default="solid", help="Image/Doodle style")
    parser.add_argument("--voice", default=None, help="Voice name/ID")
    parser.add_argument("--language", default=None, help="Language code")
    parser.add_argument("--list_voices", action="store_true", help="List voices")
    args = parser.parse_args()

    if args.list_voices:
        print("Functions to list voices skipped for brevity.")
        sys.exit(0)
    
    process_video_request(args.topic, style=args.style, voice=args.voice, language=args.language, max_beats=args.max_beats)

if __name__ == "__main__":
    main()
