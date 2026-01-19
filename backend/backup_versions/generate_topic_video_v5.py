#!/usr/bin/env python3
"""
Generate Topic Video V5 (VLM-Driven Segmented Beats)
1. Generate Beat Manifest (Topic -> Beats).
2. Generate Image for Beat (Fal.ai).
3. Analyze Image with VLM (OpenRouter):
   - Identify visual parts (bounding boxes).
   - Generate specific narration for each part.
   - Order them logically.
4. Generate Audio for each part (ElevenLabs).
5. Generate Segmented Doodle Video (DoodleVideoGeneratorV5).
6. Stitch.
"""

import os
import sys
import json
import time
import argparse
import requests
import base64
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
from dotenv import load_dotenv

load_dotenv()

# Add scripts dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from create_doodle_video_v5 import DoodleVideoGeneratorV5

# --- CONFIGURATION ---

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
FAL_KEY = os.environ.get("FAL_KEY")
ELEVEN_LABS_KEY = os.environ.get("ELEVEN_LABS_API_KEY")

# Models
GROK_MODEL = "x-ai/grok-4.1-fast" # For text mainifest
VLM_MODEL = "google/gemini-2.0-flash-exp:free" # For image analysis (or "openai/gpt-4o")
# VLM_MODEL = "openai/gpt-4o-2024-08-06"
ELEVEN_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"

def log(msg):
    print(f"[TopicVideoV5] {msg}", flush=True)

def ensure_keys():
    global OPENROUTER_API_KEY, FAL_KEY, ELEVEN_LABS_KEY
    if not OPENROUTER_API_KEY:
        log("❌ Missing OPENROUTER_API_KEY")
        sys.exit(1)
    if not FAL_KEY:
        log("❌ Missing FAL_KEY")
        sys.exit(1)
    if not ELEVEN_LABS_KEY:
        log("❌ Missing ELEVEN_LABS_API_KEY")
        sys.exit(1)

# --- 1. MANIFEST GENERATION (BEATS) ---

def generate_beat_manifest(topic):
    log(f"🧠 Generating Beat Manifest for: {topic}...")
    
    prompt = f"""
    You are a whiteboard video script expert.
    Create a video script for: "{topic}".
    
    ### GOAL
    Create 3-5 Visual Beats. Each beat shows ONE RICH image.
    
    ### FLEXIBLE SEGMENTATION (SMART LAYOUT)
    Choose 1, 2, or 3 parts based on the content structure:
    
    [1 PART] Single concept, one main idea.
    [2 PARTS] Comparisons, before/after, cause/effect.
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
          "image_prompt": "Whiteboard diagram flowing left to right: [Element A] then [Element B] then [Element C]. NO visible divider lines, natural flow.",
          "parts": [
            {{"position": 0, "visual_desc": "Element A on left side", "audio_script": "First, we have..."}},
            {{"position": 1, "visual_desc": "Element B in center", "audio_script": "This leads to..."}},
            {{"position": 2, "visual_desc": "Element C on right side", "audio_script": "Finally, we get..."}}
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

def generate_image_fal(prompt, output_path, style="color"):
    # STYLE SELECTION
    if style == "sketch":
        # CLASSIC SKETCH - black ink on white
        style_suffix = ", classic whiteboard diagram, black ink sketch on pure white background, minimal clean lines, simple icons, clear text labels, hand-drawn style, high contrast, educational, natural flow"
        negative_prompt = "color, colored, complex, filled, gradients, photo, realistic, dark background, blue background, blurry, vertical lines, divider lines, section borders, grid lines"
    else:
        # COLORFUL WHITEBOARD (Default)
        style_suffix = ", colorful whiteboard diagram on pure white background, colored pencil style, bright colored boxes and arrows, colored text labels (blue, red, green, orange), thick colorful lines, hand-drawn educational diagram, vibrant colors on white, easy to read, natural flow"
        negative_prompt = "grayscale, black and white, monochrome, dull, dark background, plain, boring, tiny text, cramped, 3d, realistic, photo, vertical lines, divider lines, section borders, grid lines"
        
    full_prompt = prompt + style_suffix
    
    log(f"🎨 Generating Image: {prompt[:40]}...")
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

# --- 3. VLM ANALYSIS ---

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image_beat(image_path, context_goal, beat_id):
    log(f"👁️ Analyzing Image for Beat {beat_id}...")
    base64_image = encode_image(image_path)
    
    prompt = f"""
    Look at this diagram about: "{context_goal}".
    
    Generate ONE short audio script to explain this entire image.
    
    ### RULES:
    - ONE script only, not multiple parts
    - Maximum 2-3 sentences (about 10-15 seconds when spoken)
    - EXPLAIN the concept, don't describe visual positions
    - Be concise and educational
    
    ### EXAMPLE GOOD SCRIPT:
    "Direct current flows in one direction from the battery through the circuit. The electrons move steadily, providing constant voltage to power the light bulb."
    
    Format: JSON
    {{
      "parts": [
        {{ "id": 1, "label": "Main Explanation", "bbox_2d": [0, 0, 1000, 1000], "script": "Your 2-3 sentence explanation here" }}
      ]
    }}
    """
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://learning-software.local",
    }

    payload = {
        "model": VLM_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }
        ],
        "response_format": {"type": "json_object"}
    }
    
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    def get_session():
        session = requests.Session()
        retry = Retry(
            total=5,
            read=5,
            connect=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    session = get_session()
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            resp = session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            content = resp.json()['choices'][0]['message']['content']
            # Clean markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                 content = content.split("```")[1].split("```")[0]
            return json.loads(content)
        except Exception as e:
            log(f"⚠️ VLM Error (Attempt {attempt+1}/{max_retries}): {e}")
            # Retry on Rate Limit OR SSL/Connection errors
            if any(x in str(e) for x in ["429", "Too Many Requests", "SSL", "Connection"]):
                wait_time = (attempt + 1) * 2
                log(f"   Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Break on other errors (like 400 Bad Request)
                # But sometimes API returns 500/502 which are retriable
                if attempt < max_retries - 1:
                     time.sleep(2)
                else:
                    break
    
    return None

# --- AUDIO ---

def generate_audio_part(text, output_path):
    # log(f"   🎙️ Audio: {text[:30]}...")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
    headers = {"xi-api-key": ELEVEN_LABS_KEY, "Content-Type": "application/json"}
    payload = {"text": text, "model_id": "eleven_turbo_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}
    
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
    parser.add_argument("--output_dir", default="topic_videos_v5", help="Output dir")
    parser.add_argument("--max_beats", type=int, default=0)
    parser.add_argument("--vlm_model", default="openai/gpt-4o", help="VLM Model to use (default: openai/gpt-4o)")
    parser.add_argument("--style", default="sketch", choices=["color", "sketch"], help="Image style: 'sketch' (default) or 'color'")
    args = parser.parse_args()

    ensure_keys()
    
    # Override global based on args
    global VLM_MODEL
    VLM_MODEL = args.vlm_model
    
    safe_topic = args.topic.lower().replace(" ", "_")
    work_dir = os.path.join(args.output_dir, safe_topic)
    os.makedirs(work_dir, exist_ok=True)
    
    # 1. Manifest
    manifest = generate_beat_manifest(args.topic)
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
        
        # A. Generate Image from manifest's image_prompt
        if not os.path.exists(image_path):
            if not generate_image_fal(beat["image_prompt"], image_path, style=args.style): 
                continue
        
        # B. Get parts from beat (or fall back to single narrator_script)
        parts = beat.get("parts", [])
        
        # Fallback: if no parts, create single part from narrator_script
        if not parts:
            narrator_script = beat.get("narrator_script", beat.get("context_goal", ""))
            if narrator_script:
                parts = [{"position": 0, "audio_script": narrator_script, "visual_desc": "full"}]
            else:
                log("❌ No parts or narrator_script in beat. Skipping.")
                continue
        
        # C. Generate audio for each part and collect durations
        audio_clips = []
        segments = []  # For doodle generator: [{position, duration}]
        
        for p_idx, part in enumerate(parts):
            p_audio_path = os.path.join(work_dir, f"{base_name}_part_{p_idx}.mp3")
            p_script = part.get("audio_script", "")
            p_position = part.get("position", p_idx)
            
            if not p_script:
                log(f"   ⚠️ Part {p_idx} has no audio_script. Skipping.")
                continue
            
            if not os.path.exists(p_audio_path):
                if not generate_audio_part(p_script, p_audio_path):
                    continue
            
            try:
                ac = AudioFileClip(p_audio_path)
                audio_clips.append(ac)
                segments.append({
                    "position": p_position,
                    "duration": ac.duration + 0.3  # Small pause between parts
                })
                log(f"   🎙️ Part {p_idx}: {ac.duration:.1f}s - {p_script[:35]}...")
            except Exception as e:
                log(f"   ⚠️ Audio read error for part {p_idx}: {e}")
        
        if not audio_clips:
            log("❌ No audio parts generated. Skipping beat.")
            continue
        
        # D. Combine audio clips
        full_audio = concatenate_audioclips(audio_clips)
        total_duration = full_audio.duration + 1.0  # Small buffer to ensure doodle completes
        
        log(f"   📊 {len(segments)} segments, total duration: {total_duration:.1f}s")
        
        # E. Generate Doodle Video with progressive segment reveal
        if not os.path.exists(final_beat_path):
            try:
                from create_doodle_video_v5 import DoodleVideoGeneratorV5
                gen = DoodleVideoGeneratorV5(
                    image_path, 
                    final_beat_path, 
                    segments=segments,  # Pass segment info for progressive reveal
                    duration=total_duration
                )
                gen.generate()
            except Exception as e:
                log(f"❌ Doodle Video Error: {e}")
                continue
        
        # F. Combine video + audio
        try:
            video_clip = VideoFileClip(final_beat_path)
            video_clip = video_clip.set_audio(full_audio)
            final_clips.append(video_clip)
            log(f"   ✅ Beat {beat_id} ready ({total_duration:.1f}s)")
        except Exception as e:
            log(f"❌ Mux Error: {e}")
            
    # Final Stitch
    if final_clips:
        log("\n🎞️ Stitching...")
        out_path = os.path.join(work_dir, f"video_v5_{safe_topic}.mp4")
        concatenate_videoclips(final_clips).write_videofile(out_path, codec="libx264", audio_codec="aac")
        log(f"🎉 Done: {out_path}")
    else:
        log("❌ No clips generated.")

if __name__ == "__main__":
    main()
