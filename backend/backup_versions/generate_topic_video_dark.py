#!/usr/bin/env python3
"""
Generate Topic Video V4 (Beat-Based Progressive Generation)
Automates video creation by breaking topics into granular "Visual Beats" for perfect sync.

Pipeline:
1. OpenRouter (Grok/LLM): Generates a JSON manifest of "Visual Beats".
   - Beat 1: "Show Empty Stack"
   - Beat 2: "Show 1 Item in Stack"
   - Each beat has a specific [Image Prompt] + [Narrator Script].
2. Fal.ai: Generates the image for EACH beat.
3. ElevenLabs: Generates audio for EACH beat.
4. DoodleVideoGenerator: Draws the beat's image quickly (Fast Draw).
5. MoviePy: Stitches beats together.
"""

import os
import sys
import json
import time
import argparse
import requests
import uuid
import numpy as np
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from dotenv import load_dotenv

load_dotenv()

# Add scripts dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from create_doodle_video import DoodleVideoGenerator

# --- CONFIGURATION ---

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
FAL_KEY = os.environ.get("FAL_KEY")
ELEVEN_LABS_KEY = os.environ.get("ELEVEN_LABS_API_KEY")

GROK_MODEL = "x-ai/grok-4.1-fast"
ELEVEN_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb" # Default voice

def log(msg):
    print(f"[TopicVideoV4] {msg}", flush=True)

def ensure_keys():
    # Helper to check keys again if env vars were just set
    global OPENROUTER_API_KEY, FAL_KEY, ELEVEN_LABS_KEY
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    FAL_KEY = os.environ.get("FAL_KEY")
    ELEVEN_LABS_KEY = os.environ.get("ELEVEN_LABS_API_KEY")
    
    if not OPENROUTER_API_KEY:
        log("❌ Missing OPENROUTER_API_KEY")
        sys.exit(1)
    if not FAL_KEY:
        log("❌ Missing FAL_KEY")
        sys.exit(1)
    if not ELEVEN_LABS_KEY:
        log("❌ Missing ELEVEN_LABS_API_KEY")
        sys.exit(1)

# --- 1. SCRIPT GENERATION (BEATS) ---

def generate_beat_manifest(topic):
    log(f"🧠 Generating Beat Manifest for: {topic}...")
    
    prompt = f"""
    You are a technical documentation expert.
    Create a video script for: "{topic}".
    
    ### GOAL
    Explain the algorithm/concept with EXTREME CLARITY and PRECISION.
    
    ### FORMAT: "VISUAL BEATS"
    Break the topic into 5-8 granular steps.
    
    ### CRITICAL VISUAL INSTRUCTIONS: DARK MODE DOODLE
    - **Style**: CLEAN LINE ART on PURE BLACK BACKGROUND.
    - **Aesthetic**: White lines on Black. High Contrast. Minimalist.
    - **Color**: White (Primary), Neon Blue/Pink (Highlights).
    - **NO**: No chalkboard texture, no dust, no photorealism.
    - **Content**:
      - Describe the visuals as "White line diagram on black background of..."
      - Use clear, correct shapes for technical accuracy.
      - "Diagram of a Neural Network", "Chart showing X vs Y".
    
    ### CRITICAL AUDIO INSTRUCTIONS
    - **Concise**: Max 2 sentences per beat (10-12s).
    - **Direct**: Explain exactly what the visual represents.
    - **NO FORMULA DICTATION**: Do NOT read formulas aloud.
    
    ### TARGET OUPUT (JSON ONLY)
    {{
      "topic": "{topic}",
      "beats": [
        {{ "beat_id": 1, "image_prompt": "White line diagram on black background of..., Label: '...'", "narrator_script": "..." }},
        {{ "beat_id": 2, "image_prompt": "...", "narrator_script": "..." }}
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
        data = resp.json()
        content = data['choices'][0]['message']['content']
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        return json.loads(content)
    except Exception as e:
        log(f"❌ Script Generation Error: {e}")
        return None

# --- 2. ASSET GENERATION ---

def generate_audio_elevenlabs(text, output_path):
    log(f"🎙️ Generating audio: {text[:40]}...")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVEN_LABS_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(resp.content)
        return True
    except Exception as e:
        log(f"❌ Audio Gen Error: {e}")
        return False

def generate_image_fal(prompt, output_path):
    style_suffix = ", white chalk on blackboard, clean white lines, dark background, high contrast, minimalist, no shading"
    full_prompt = prompt + style_suffix
    
    log(f"🎨 Generating image: {prompt[:40]}...")
    # Using User-Request Model: fal-ai/nano-banana
    url = "https://fal.run/fal-ai/nano-banana" 
    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": full_prompt,
        # Trying standard params first
        "image_size": "landscape_16_9", 
        "num_inference_steps": 4, 
        "enable_safety_checker": False
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        if 'images' in result and len(result['images']) > 0:
            image_url = result['images'][0]['url']
            img_resp = requests.get(image_url)
            img_resp.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(img_resp.content)
            return True
        else:
             log(f"❌ No image in response: {result}")
             return False
    except Exception as e:
        log(f"❌ Image Generation Error: {e}")
        return False

# --- MAIN FLOW ---

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", help="Topic title to generate video for")
    parser.add_argument("--output_dir", default="topic_videos_v4", help="Output directory")
    parser.add_argument("--max_beats", type=int, default=0, help="Limit number of beats (0 = no limit)")
    args = parser.parse_args()

    ensure_keys()
    
    safe_topic = args.topic.lower().replace(" ", "_")
    work_dir = os.path.join(args.output_dir, safe_topic)
    os.makedirs(work_dir, exist_ok=True)
    
    # 1. Generate Manifest
    manifest = generate_beat_manifest(args.topic)
    if not manifest:
        sys.exit(1)
        
    beats = manifest.get("beats", [])
    
    # Apply max_beats limit if specified
    if args.max_beats > 0:
        beats = beats[:args.max_beats]
    
    log(f"📜 Processing {len(beats)} beats for '{args.topic}'...")
    
    final_clips = []
    
    for i, beat in enumerate(beats):
        beat_id = i + 1
        log(f"\n--- Processing Beat {beat_id} ---")
        
        base_name = f"beat_{beat_id}"
        audio_path = os.path.join(work_dir, f"{base_name}.mp3")
        image_path = os.path.join(work_dir, f"{base_name}.png")
        video_path = os.path.join(work_dir, f"{base_name}_doodle.mp4")
        
        # A. Audio
        if not os.path.exists(audio_path):
            if not generate_audio_elevenlabs(beat["narrator_script"], audio_path):
                continue
        
        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            audio_clip.close()
            log(f"   Audio Duration: {duration:.2f}s")
        except Exception as e:
            log(f"❌ Failed to read audio duration: {e}")
            continue

        # B. Image
        if not os.path.exists(image_path):
            if not generate_image_fal(beat["image_prompt"], image_path):
                continue
        
        # C. Doodle Video (Fast Draw)
        # We rely on DoodleVideoGenerator's internal heuristic to draw quickly (<3.5s)
        # We pass drawing_duration=None so it calculates it (min(3.5, dur*0.8))
        
        if not os.path.exists(video_path):
            log(f"   Generating Doodle Video (Fast Draw)...")
            try:
                # We enforce the video to be exactly length of audio (+ small buffer for comfort)
                # But the drawing will finish early due to internal logic
                gen = DoodleVideoGenerator(image_path, video_path, duration=duration + 0.1)
                gen.generate()
            except Exception as e:
                log(f"❌ Doodle Generation Failed: {e}")
                continue

        # D. Combine
        try:
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            
            final_duration = max(video_clip.duration, audio_clip.duration)
            video_clip = video_clip.set_audio(audio_clip)
            final_clips.append(video_clip)
            log(f"   ✅ Beat {beat_id} ready.")
            
        except Exception as e:
            log(f"❌ Clip merging failed: {e}")

    # 3. Concatenate
    if final_clips:
        log("\n🎞️ Stitching final video...")
        final_output = os.path.join(work_dir, f"video_v4_{safe_topic}.mp4")
        try:
            final_video = concatenate_videoclips(final_clips)
            final_video.write_videofile(final_output, codec="libx264", audio_codec="aac")
            log(f"🎉 Success! Video saved to: {final_output}")
        except Exception as e:
             log(f"❌ Final concatenation failed: {e}")
    else:
        log("❌ No clips were generated successfully.")

if __name__ == "__main__":
    main()
