#!/usr/bin/env python3
"""
Generate Topic Video V2 (Doodle Style)
Automates the creation of a full educational video from a single topic text.
Improvements in V2:
- Narration: Explicitly forbids reading formulas verbatim; focuses on conceptual explanation.
- visuals: Enforces Left-to-Right layout in image prompts to better align with drawing order.

Pipeline:
1. Grok (OpenRouter): Generates a script with narration and "technical pencil" image prompts.
2. ElevenLabs: Generates high-quality narration audio.
3. Fal.ai (Imagen 4): Generates clean, labelled diagram images.
4. DoodleVideoGenerator: Converts images + audio duration into doodle animations.
5. MoviePy: Stitches everything into a final MP4.
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

# Add scripts dir to path to allow importing create_doodle_video
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from create_doodle_video import DoodleVideoGenerator

from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

# --- CONFIGURATION ---

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("VITE_OPENROUTER_API_KEY")
FAL_KEY = os.environ.get("FAL_KEY") or os.environ.get("FAL_KEY_SECRET")
ELEVEN_LABS_KEY = os.environ.get("ELEVEN_LABS_API_KEY") or "sk_7c32ab097cad888a7804ea29b3f56510785c506c321a05fc"

GROK_MODEL = "x-ai/grok-4.1-fast"
ELEVEN_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb" # Default voice

def log(msg):
    print(f"[TopicVideo] {msg}", flush=True)

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

# --- 1. SCRIPT GENERATION (GROK) ---

def generate_script_manifest(topic):
    log(f"🧠 Generating script for: {topic}...")
    
    # CRITICAL: Prompt engineering for "Clean Explanatory" images & Natural Narration
    image_style_guide = (
        "Technical pencil drawing style, white background, high contrast, clean single strokes. "
        "No shading, just clear outlines and text. "
        "Must have bold, clear text labels for components. "
    )

    prompt = f"""
    You are an expert educational content creator.
    Create a video script for an educational video about: "{topic}".
    
    1. First, analyze the complexity of this topic. 
       - Simple/Introductory: ~3 scenes.
       - Intermediate/Process: ~5 scenes.
       - Complex/Deep Dive: ~7 scenes.
    
    2. For EACH scene, provide:
       - "narrator_script": The exact text for the voiceover.
         - CRITICAL: DO NOT read formulas symbol-by-symbol (e.g. do not say "square root of x plus y equals"). 
         - Instead, explain the *concept* or *meaning* of the formula naturally.
         - Make it conversational and engaging, like a teacher explaining to a student.
       
       - "image_prompt": A highly specific description for a clean explanatory diagram.
         - CRITICAL: The image prompt MUST specify a "{image_style_guide}".
         - LAYOUT INSTRUCTION: Describe the diagram such that it flows from LEFT to RIGHT. (e.g. "Input on the left, Process in the middle, Output on the right"). This matches our drawing animation engine.
         - Describe exactly what labels should appear.
    
    Respond with this JSON structure ONLY:
    {{
      "topic": "{topic}",
      "complexity": "...",
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
        
        # Clean potential markdown wrappers
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        return json.loads(content)
    except Exception as e:
        log(f"❌ Script Generation Error: {e}")
        return None

# --- 2. AUDIO GENERATION (ELEVENLABS) ---

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

# --- 3. IMAGE GENERATION (FAL.AI) ---

def generate_image_fal(prompt, output_path):
    # Enforce the style one last time in case Grok missed it
    style_suffix = ", technical pencil drawing, white background, single clean bold strokes, no shading, no texture, high contrast diagram, minimalist"
    full_prompt = prompt + style_suffix
    
    log(f"🎨 Generating image: {prompt[:40]}...")

    # Switch to Imagen 4 
    url = "https://fal.run/fal-ai/imagen4/preview/ultra" 
    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": full_prompt,
        "negative_prompt": "shading, shadows, texture, noise, fuzzy, sketch lines, messy, grey, gradient, 3d render, photo, realistic, complex background, grid, dots, colored, artistic",
        "aspect_ratio": "16:9"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        if 'images' in result and len(result['images']) > 0:
            image_url = result['images'][0]['url']
            
            # Download
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
    parser.add_argument("--output_dir", default="topic_videos_v2", help="Output directory")
    args = parser.parse_args()

    ensure_keys()
    
    # 1. Setup
    safe_topic = args.topic.lower().replace(" ", "_")
    work_dir = os.path.join(args.output_dir, safe_topic)
    os.makedirs(work_dir, exist_ok=True)
    
    # 2. Generate Script
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
                
        # C. Doodle Video
        # We generate the video to match audio duration + 0.5s buffer
        target_duration = duration + 0.5
        
        if not os.path.exists(video_path):
            log(f"   Generating Doodle Video ({target_duration:.2f}s)...")
            try:
                gen = DoodleVideoGenerator(image_path, video_path, duration=target_duration)
                gen.generate()
            except Exception as e:
                log(f"❌ Doodle Generation Failed: {e}")
                continue

        # D. Combine Audio + Video
        try:
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            
            # Trim/Extend video to exact audio length if needed, or keeping it loose
            # Usually better to let the video finish drawing.
            # If video is shorter than audio, freeze last frame.
            # If video is longer (drawing took long), let it play.
            
            final_duration = max(video_clip.duration, audio_clip.duration)
            video_clip = video_clip.set_audio(audio_clip)
            final_clips.append(video_clip)
            log(f"   ✅ Scene {seg_id} ready.")
            
        except Exception as e:
            log(f"❌ Clip merging failed: {e}")

    # 3. Concatenate
    if final_clips:
        log("\n🎞️ Stitching final video...")
        final_output = os.path.join(work_dir, f"final_{safe_topic}.mp4")
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
