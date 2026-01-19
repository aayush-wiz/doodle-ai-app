#!/usr/bin/env python3
"""
Generate Topic Video V7 (Structure-First / No-AI Logic)
1. Generate Beat Manifest (Topic -> Simple Beats).
2. Generate Image (Fal.ai).
3. Generate Audio.
4. Generate Video using `DoodleVideoGeneratorV7` (Algorithmic Sorting).
   - No VLM / Bounding Boxes required.
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
from create_doodle_video_v7 import DoodleVideoGeneratorV7

# --- CONFIGURATION ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
FAL_KEY = os.environ.get("FAL_KEY")
ELEVEN_LABS_KEY = os.environ.get("ELEVEN_LABS_API_KEY")

GROK_MODEL = "x-ai/grok-4.1-fast"
ELEVEN_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"

def log(msg):
    print(f"[TopicVideoV7] {msg}", flush=True)

def ensure_keys():
    if not all([OPENROUTER_API_KEY, FAL_KEY, ELEVEN_LABS_KEY]):
        log("❌ Missing API Keys (OpenRouter, Fal, or ElevenLabs)")
        sys.exit(1)

# --- 1. MANIFEST (Simplified) ---

def generate_beat_manifest(topic):
    log(f"🧠 Generating V7 Manifest for: {topic}...")
    
    prompt = f"""
    You are a whiteboard video script expert.
    Create a video script for: "{topic}".
    
    ### CRITICAL: VISUALLY DESCRIPTIVE NARRATION
    The narration must NOT just be abstract explanation.
    It MUST explicitly guide the viewer's eye across the diagram using spatial cues.
    
    ### STRUCTURE
    1. **General Concept:** Briefly explain the "Why" or "What".
    2. **Visual Walkthrough:** Explicitly point to the image parts ("As you can see on the left...", "In the center...", "Flowing to the right...").
    
    ❌ BAD (Abstract): "The engine burns fuel to create power. The piston moves up and down."
    ✅ GOOD (Descriptive): "The engine burns fuel to create power. **As you can see on the left**, fuel enters the chamber... **Here in the center**, the piston compresses it... and **on the right**, exhaust is released."

    ### GOAL
    Create 3-5 Visual Beats.
    Each beat has ONE RICH IMAGE and ONE NARRATION SCRIPT.
    
    ### OUTPUT (JSON ONLY)
    {{
      "topic": "{topic}",
      "beats": [
        {{ 
          "beat_id": 1,
          "image_prompt": "A complex diagram of X showing A, B, C...",
          "narrator_script": "Let's look at X. [Concept]. Starting on the left, we see [Part A]... Moving to the center, [Part B] does [Action]..."
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
    parser.add_argument("--output_dir", default="topic_videos_v7", help="Output dir")
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
        audio_path = os.path.join(work_dir, f"{base_name}.mp3")
        video_path = os.path.join(work_dir, f"{base_name}_doodle.mp4")
        
        # A. Image
        if not os.path.exists(image_path):
            if not generate_image_fal(beat["image_prompt"], image_path, style=args.style): 
                continue

        # B. Audio
        script = beat.get("narrator_script", "")
        if not script: 
            log("❌ No script. Skipping.")
            continue
            
        if not os.path.exists(audio_path):
            generate_audio_part(script, audio_path)
            
        # C. Doodle (Structure-First)
        try:
            ac = AudioFileClip(audio_path)
            duration = ac.duration + 1.0 # Buffer
            
            if not os.path.exists(video_path):
                gen = DoodleVideoGeneratorV7(image_path, video_path, duration=duration)
                gen.generate()
                
            # D. Mux
            video_clip = VideoFileClip(video_path)
            video_clip = video_clip.set_audio(ac)
            final_clips.append(video_clip)
            log(f"   ✅ Beat {beat_id} ready.")
            
        except Exception as e:
            log(f"❌ Processing Error: {e}")

    # Final Stitch
    if final_clips:
        out_path = os.path.join(work_dir, f"video_v7_{safe_topic}.mp4")
        concatenate_videoclips(final_clips).write_videofile(out_path, codec="libx264", audio_codec="aac")
        log(f"🎉 Done: {out_path}")
    else:
        log("❌ No clips.")

if __name__ == "__main__":
    main()
