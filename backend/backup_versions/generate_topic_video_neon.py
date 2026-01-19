#!/usr/bin/env python3
"""
Generate Topic Video NEON (Based on V4)
Creates Neon/Cyberpunk style videos with Black Backgrounds.
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

# Load env vars
load_dotenv()

# Add scripts dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from create_neon_video import NeonVideoGenerator

# --- CONFIGURATION ---

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
FAL_KEY = os.environ.get("FAL_KEY")
ELEVEN_LABS_KEY = os.environ.get("ELEVEN_LABS_API_KEY")

GROK_MODEL = "openai/gpt-4o"
ELEVEN_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb" # Default voice

def log(msg):
    print(f"[TopicVideoNEON] {msg}", flush=True)

def ensure_keys():
    global OPENROUTER_API_KEY, FAL_KEY, ELEVEN_LABS_KEY
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    FAL_KEY = os.environ.get("FAL_KEY")
    ELEVEN_LABS_KEY = os.environ.get("ELEVEN_LABS_API_KEY")
    
    if not OPENROUTER_API_KEY or not FAL_KEY or not ELEVEN_LABS_KEY:
        log("❌ Missing API Keys")
        sys.exit(1)

# --- 1. SCRIPT GENERATION (BEATS) ---

def generate_beat_manifest(topic):
    log(f"🧠 Generating Neon Manifest for: {topic}...")
    
    prompt = f"""
    You are a technical documentation expert.
    Create a video script for: "{topic}".
    
    ### CRITICAL VISUAL INSTRUCTIONS: NEON EXPLAINER STYLE
    - **Style**: HAND-DRAWN DIAGRAM on DARK GLASS BOARD.
    - **Aesthetic**: Use NEON MARKERS (glowing lines) on a black surface.
    - **Color**: Cyan (Structure), Magenta (Action), Lime (Data).
    - **Content**:
      - **Goal**: EXPLAIN the concept visually (like a professor drawing on a lightboard).
      - **Detail**: Rich, informative diagrams. NOT simple icons.
      - **Flow**: Prefer Left-to-Right or Top-to-Down flow for processes.
      - **Text**: Include clear, readable labels for key parts.
    
    ### EXAMPLES OF GOOD PROMPTS:
    
    **System Architecture:**
    "A neon diagram on dark glass showing a Load Balancer.
     1. Left: 'Users' (multiple icons) sending requests.
     2. Center: 'Load Balancer' box distributing traffic.
     3. Right: Three 'Servers' receiving data.
     4. Arrows: Flowing left to right, labeled 'HTTP'.
     Style: Detailed, technical, glowing."
    
    **Process Flow:**
    "A neon flowchart explaining Photosynthesis.
     1. Sun (top) sends rays to Leaf (center).
     2. Inputs: 'CO2' and 'Water' entering.
     3. Process: Internal cycle shown with arrows.
     4. Output: 'Oxygen' and 'Sugar' leaving.
     Style: Educational science diagram."
    
    ### WHAT TO AVOID:
    - ❌ BAD: "A cool abstract neon city." (No educational value)
    - ❌ BAD: "A simple square." (Too basic)
    - ❌ BAD: "Photorealistic person." (Keep it to diagrams/stick figures if needed, or just shapes)
    
    ### TARGET OBJETIVE
    Create a "Lightboard" style educational video.
    
    ### TARGET OUPUT (JSON ONLY)
    {{
      "topic": "{topic}",
      "beats": [
        {{ "beat_id": 1, "image_prompt": "Neon diagram on dark glass showing... (Descriptive & Educational)", "narrator_script": "First, we take the [Input]..." }},
        {{ "beat_id": 2, "image_prompt": "...", "narrator_script": "..." }}
      ]
    }}
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
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
    headers = {"xi-api-key": ELEVEN_LABS_KEY, "Content-Type": "application/json"}
    payload = {"text": text, "model_id": "eleven_turbo_v2"}
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
    # NEON STYLE PROMPT
    style_suffix = ", neon art style, black background, glowing neon lines, cyan and magenta theme, high contrast, cyberpunk, dark mode, minimalist vector graphics"
    full_prompt = prompt + style_suffix
    
    log(f"🎨 Generating Neon image: {prompt[:40]}...")
    url = "https://fal.run/fal-ai/nano-banana" 
    headers = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}
    payload = {
        "prompt": full_prompt,
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
             log(f"❌ No image in response")
             return False
    except Exception as e:
        log(f"❌ Image Generation Error: {e}")
        return False

# --- MAIN FLOW ---

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", help="Topic title")
    parser.add_argument("--output_dir", default="topic_videos_neon", help="Output directory")
    parser.add_argument("--max_beats", type=int, default=0, help="Limit beats")
    args = parser.parse_args()

    ensure_keys()
    
    safe_topic = args.topic.lower().replace(" ", "_")
    work_dir = os.path.join(args.output_dir, safe_topic)
    os.makedirs(work_dir, exist_ok=True)
    
    manifest = generate_beat_manifest(args.topic)
    if not manifest: sys.exit(1)
        
    beats = manifest.get("beats", [])
    if args.max_beats > 0:
        beats = beats[:args.max_beats]
    
    log(f"📜 Processing {len(beats)} NEON beats for '{args.topic}'...")
    
    final_clips = []
    
    for i, beat in enumerate(beats):
        beat_id = i + 1
        log(f"\n--- Processing Beat {beat_id} ---")
        
        base_name = f"beat_{beat_id}"
        audio_path = os.path.join(work_dir, f"{base_name}.mp3")
        image_path = os.path.join(work_dir, f"{base_name}.png")
        video_path = os.path.join(work_dir, f"{base_name}_neon.mp4")
        
        if not os.path.exists(audio_path):
            if not generate_audio_elevenlabs(beat["narrator_script"], audio_path): continue
        
        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            audio_clip.close()
        except: continue

        if not os.path.exists(image_path):
            if not generate_image_fal(beat["image_prompt"], image_path): continue
        
        if not os.path.exists(video_path):
            log(f"   Generating Neon Animation...")
            try:
                # Use NeonVideoGenerator
                gen = NeonVideoGenerator(image_path, video_path, duration=duration + 0.1)
                gen.generate()
            except Exception as e:
                log(f"❌ Animation Failed: {e}")
                continue

        try:
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            final_duration = max(video_clip.duration, audio_clip.duration)
            video_clip = video_clip.set_audio(audio_clip)
            final_clips.append(video_clip)
            log(f"   ✅ Beat {beat_id} ready.")
        except: pass

    if final_clips:
        log("\n🎞️ Stitching final video...")
        final_output = os.path.join(work_dir, f"video_neon_{safe_topic}.mp4")
        try:
            final_video = concatenate_videoclips(final_clips)
            final_video.write_videofile(final_output, codec="libx264", audio_codec="aac")
            log(f"🎉 Success! Video saved to: {final_output}")
        except Exception as e:
             log(f"❌ Final concatenation failed: {e}")

if __name__ == "__main__":
    main()
