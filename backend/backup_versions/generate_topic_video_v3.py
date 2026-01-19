#!/usr/bin/env python3
"""
Generate Topic Video V3 (Coupled Image-First Generation)
Automates the creation of a doodle video where the script is strictly grounded in the visual.

Pipeline:
1. OpenRouter (Grok/LLM): Generates a JSON manifest containing [Image Prompt] + [Narrator Script].
   - CRITICAL: The prompt enforces that the script describes ONLY what is in the image.
2. Fal.ai: Generates the image from the prompt.
3. ElevenLabs: Generates audio from the script.
4. DoodleVideoGenerator (V2): Animates the image L->R synced to audio duration.
5. MoviePy: Stitches segments.
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

# Add scripts dir to path to import create_doodle_video
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from create_doodle_video import DoodleVideoGenerator

# --- CONFIGURATION ---

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("VITE_OPENROUTER_API_KEY")
FAL_KEY = os.environ.get("FAL_KEY") or os.environ.get("FAL_KEY_SECRET")
ELEVEN_LABS_KEY = os.environ.get("ELEVEN_LABS_API_KEY") or "sk_7c32ab097cad888a7804ea29b3f56510785c506c321a05fc"

GROK_MODEL = "x-ai/grok-4.1-fast"
ELEVEN_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb" # Default voice

def log(msg):
    print(f"[TopicVideoV3] {msg}", flush=True)

def ensure_keys():
    if not OPENROUTER_API_KEY:
        log("❌ Missing OPENROUTER_API_KEY")
        sys.exit(1)
    if not FAL_KEY:
        log("❌ Missing FAL_KEY")
        sys.exit(1)
    if not ELEVEN_LABS_KEY:
        log("❌ Missing ELEVEN_LABS_API_KEY")
        sys.exit(1)

# --- 1. COUPLED GENERATION (LLM) ---

def generate_script_manifest(topic):
    log(f"🧠 Generating Coupled Manifest for: {topic}...")
    
    prompt = f"""
    You are an expert educational content creator.
    Create a video script for an educational video about: "{topic}".
    
    You must generate TWO distinct outputs for each scene:
    1. **The Visual Prompt**: Instructions for an AI artist to draw a diagram.
    2. **The Explainer Script**: The voiceover that explains the *topic* shown in the diagram.
    
    CRITICAL CONSTRAINT - LEFT-TO-RIGHT TIMING:
    The video is an animation where the diagram is drawn from Left to Right.
    The script must match this flow.
    
    For each scene, follow this process:
    
    ### TASK 1: CREATE THE IMAGE PROMPT (`image_prompt`)
    - Design a clean, technical pencil drawing.
    - Layout MUST flow linearly from **Left to Right**.
    - Describe the visual elements concretely (e.g. "A stack of plates on the left, an arrow pointing right").
    
    ### TASK 2: CREATE THE EXPLAINER SCRIPT (`narrator_script`)
    - Write the voiceover that explains the **educational concept** shown in the image.
    - **STRICT PROHIBITION**: DO NOT mention the drawing process.
      - ❌ BAD: "Now we draw a rectangle on the left."
      - ❌ BAD: "The pencil sketches a stack."
      - ✅ GOOD: "The Stack data structure works like a pile of plates." ("Stack" is the concept, "pile of plates" is the visual metaphor).
    - **SYNC RULE**: Explain the elements **in the order they appear (Left -> Right)**.
      - First sentence explains the Left element.
      - Next sentence explains the Middle/Right element.
    
    Structure:
    - Simple Topic: 3 scenes.
    - Complex Topic: 5 scenes.
    
    Respond with this JSON structure ONLY:
    {{
      "topic": "{topic}",
      "segments": [
        {{ "segment_id": 1, "image_prompt": "...", "narrator_script": "..." }},
        ...
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
    # Enforce strict style for V2 doodle logic (needs clean lines for thresholding)
    style_suffix = ", technical pencil drawing, white background, single clean bold strokes, no shading, high contrast, minimalist, black ink on white paper"
    full_prompt = prompt + style_suffix
    
    log(f"🎨 Generating image: {prompt[:40]}...")
    url = "https://fal.run/fal-ai/imagen4/preview/ultra" 
    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": full_prompt,
        "negative_prompt": "shading, shadows, texture, noise, fuzzy, sketch lines, messy, grey, gradient, 3d render, photo, realistic, color, complex",
        "aspect_ratio": "16:9"
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
    parser.add_argument("--output_dir", default="topic_videos_v3", help="Output directory")
    args = parser.parse_args()

    ensure_keys()
    
    safe_topic = args.topic.lower().replace(" ", "_")
    work_dir = os.path.join(args.output_dir, safe_topic)
    os.makedirs(work_dir, exist_ok=True)
    
    # 1. Generate Manifest
    manifest = generate_script_manifest(args.topic)
    if not manifest:
        sys.exit(1)
        
    segments = manifest.get("segments", [])
    log(f"📜 Processing {len(segments)} scenes for '{args.topic}'...")
    
    final_clips = []
    
    for i, seg in enumerate(segments):
        seg_id = i + 1
        log(f"\n--- Processing Scene {seg_id} ---")
        
        base_name = f"scene_{seg_id}"
        audio_path = os.path.join(work_dir, f"{base_name}.mp3")
        image_path = os.path.join(work_dir, f"{base_name}.png")
        video_path = os.path.join(work_dir, f"{base_name}_doodle.mp4")
        
        # A. Audio
        if not os.path.exists(audio_path):
            if not generate_audio_elevenlabs(seg["narrator_script"], audio_path):
                continue
        
        # Get duration
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
            if not generate_image_fal(seg["image_prompt"], image_path):
                continue
                
        # C. Doodle Video (Using V2 Logic with Fast Pacing)
        target_video_duration = duration # Video is exactly audio length
        drawing_duration = duration * 0.90 # Finish drawing 90% of the way through
        
        if not os.path.exists(video_path):
            log(f"   Generating Doodle Video (Vid: {target_video_duration:.2f}s, Draw: {drawing_duration:.2f}s)...")
            try:
                gen = DoodleVideoGenerator(image_path, video_path, duration=target_video_duration, drawing_duration=drawing_duration)
                gen.generate()
            except Exception as e:
                log(f"❌ Doodle Generation Failed: {e}")
                continue

        # D. Combine
        try:
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            
            # Use max to ensure we don't cut off audio or video
            final_duration = max(video_clip.duration, audio_clip.duration)
            video_clip = video_clip.set_audio(audio_clip)
            final_clips.append(video_clip)
            log(f"   ✅ Scene {seg_id} ready.")
            
        except Exception as e:
            log(f"❌ Clip merging failed: {e}")

    # 3. Concatenate
    if final_clips:
        log("\n🎞️ Stitching final video...")
        final_output = os.path.join(work_dir, f"video_v3_{safe_topic}.mp4")
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
