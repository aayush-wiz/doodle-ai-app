#!/usr/bin/env python3
"""
Generate Topic Video V6 (Logical Step-by-Step Doodle)
1. Generate Beat Manifest (Topic -> Logical Beats).
2. Generate Image for Beat (Fal.ai).
3. Analyze Image with VLM to get BOUNDING BOXES for each step.
4. Generate Audio for each step.
5. Generate Video with `DoodleVideoGeneratorV6` using bbox segments.
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

# Add scripts dir to path to find local modules if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from create_doodle_video_v6 import DoodleVideoGeneratorV6

# --- CONFIGURATION ---

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
FAL_KEY = os.environ.get("FAL_KEY")
ELEVEN_LABS_KEY = os.environ.get("ELEVEN_LABS_API_KEY")

# Models
GROK_MODEL = "x-ai/grok-4.1-fast" # For text manifest
VLM_MODEL = "openai/gpt-4o" # More stable than free Gemini for VLM tasks
ELEVEN_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"

def log(msg):
    print(f"[TopicVideoV6] {msg}", flush=True)

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
    log(f"🧠 Generating V6 Manifest for: {topic}...")
    
    prompt = f"""
    You are a whiteboard video script expert.
    Create a video script for: "{topic}".
    
    ### GOAL
    Create 3-5 Visual Beats. Each beat shows ONE RICH image (Infographic, Graph, Plot, or Diagram).
    
    ### LOGICAL SEGMENTATION (STEP-BY-STEP)
    For complex concepts, break the drawing down into LOGICAL STEPS (not just left-to-right).
    Example:
    - Step 1: Draw the axis/framework.
    - Step 2: Draw the main data curve.
    - Step 3: Draw the highlights/labels.
    
    Allow 2-4 steps per beat.
    
    ### OUTPUT (JSON ONLY)
    {{
      "topic": "{topic}",
      "beats": [
        {{ 
          "beat_id": 1,
          "image_prompt": "A complex line graph showing exponential growth vs linear growth. Clear axis labels, distinct colored lines.",
          "parts": [
            {{ "step_id": 1, "visual_desc": "The empty graph axes with labels", "audio_script": "Let's set up our graph with time on the X axis and value on the Y axis." }},
            {{ "step_id": 2, "visual_desc": "The linear growth line (straight)", "audio_script": "Linear growth adds a constant amount each time period." }},
            {{ "step_id": 3, "visual_desc": "The exponential growth curve (steep)", "audio_script": "But exponential growth multiplies, leading to a rapid skyrocket." }}
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
        style_suffix = ", classic whiteboard diagram, black ink sketch on pure white background, minimal clean lines, simple icons, clear text labels, hand-drawn style, high contrast, educational, natural flow"
        negative_prompt = "color, colored, complex, filled, gradients, photo, realistic, dark background, blue background, blurry, vertical lines, divider lines, section borders, grid lines"
    else:
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

# --- 3. VLM ANALYSIS (BBOX EXTRACTION) ---

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_bboxes_for_parts(image_path, parts):
    """
    Ask VLM to find bounding boxes for each part description.
    Returns a dict {step_id: [ymin, xmin, ymax, xmax] (0-1000)}
    """
    log(f"👁️ Detecting logical parts in image...")
    base64_image = encode_image(image_path)
    
    # Construct prompt
    part_descriptions = ""
    for p in parts:
        step_id = p.get('step_id', 0)
        desc = p.get('visual_desc', '')
        part_descriptions += f"- Step {step_id}: {desc}\n"
        
    prompt = f"""
    I have an image and a list of logical steps that explain parts of this image.
    I need you to find the Bounding Box for the visual elements corresponding to EACH step.
    
    STEPS:
    {part_descriptions}
    
    Return a JSON object with the bounding box for each step_id.
    Format: [ymin, xmin, ymax, xmax] where coordinates are 0-1000 (normalized).
    
    Example Output:
    {{
      "1": [0, 0, 1000, 500],
      "2": [500, 200, 800, 800]
    }}
    
    Make sure to cover the main elements described.
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
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
            
            if resp.status_code == 429:
                wait_time = (attempt + 1) * 5
                log(f"   ⚠️ Rate Limit (429). Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            resp.raise_for_status()
            content = resp.json()['choices'][0]['message']['content']
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)
            
        except Exception as e:
            log(f"   ⚠️ VLM Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                log(f"❌ VLM All Retries Failed.")
    return {}

# --- 4. AUDIO ---

def generate_audio_part(text, output_path):
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
    parser.add_argument("--output_dir", default="topic_videos_v6", help="Output dir")
    parser.add_argument("--max_beats", type=int, default=0)
    parser.add_argument("--style", default="sketch", choices=["color", "sketch"], help="Image style")
    args = parser.parse_args()

    ensure_keys()
    
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
        
        # A. Generate Image
        if not os.path.exists(image_path):
            if not generate_image_fal(beat["image_prompt"], image_path, style=args.style): 
                continue
        
        parts = beat.get("parts", [])
        if not parts:
            log("❌ No parts. Skipping.")
            continue
            
        # B. Get Bounding Boxes from VLM
        bboxes = get_bboxes_for_parts(image_path, parts)
        log(f"   📦 Got bboxes for {len(bboxes)} parts")
        
        # C. Generate Audio & Build Segments
        audio_clips = []
        segments = [] 
        
        for p_idx, part in enumerate(parts):
            step_id = part.get("step_id", p_idx+1)
            p_audio_path = os.path.join(work_dir, f"{base_name}_part_{p_idx}.mp3")
            p_script = part.get("audio_script", "")
            
            # Generate Audio
            if not os.path.exists(p_audio_path):
                generate_audio_part(p_script, p_audio_path)
            
            # Load duration
            try:
                ac = AudioFileClip(p_audio_path)
                audio_clips.append(ac)
                
                # Get bbox for this step (convert key to string to match JSON keys)
                bbox = bboxes.get(str(step_id)) or bboxes.get(step_id)
                if not bbox:
                    log(f"   ⚠️ No bbox for step {step_id}, might default to global sort")
                
                segments.append({
                    "step_id": step_id,
                    "duration": ac.duration + 0.5, # Pause
                    "bbox": bbox,
                    "desc": part.get("visual_desc")
                })
            except Exception as e:
                log(f"   ⚠️ Audio error part {p_idx}: {e}")

        # D. Combine Audio
        if not audio_clips: continue
        full_audio = concatenate_audioclips(audio_clips)
        total_duration = full_audio.duration + 1.0
        
        # E. Generate Doodle Video
        if not os.path.exists(final_beat_path):
            try:
                gen = DoodleVideoGeneratorV6(
                    image_path, 
                    final_beat_path, 
                    segments=segments,
                    duration=total_duration
                )
                gen.generate()
            except Exception as e:
                log(f"❌ Doodle Gen Error: {e}")
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
        out_path = os.path.join(work_dir, f"video_v6_{safe_topic}.mp4")
        concatenate_videoclips(final_clips).write_videofile(out_path, codec="libx264", audio_codec="aac")
        log(f"🎉 Done: {out_path}")
    else:
        log("❌ No clips.")

if __name__ == "__main__":
    main()
