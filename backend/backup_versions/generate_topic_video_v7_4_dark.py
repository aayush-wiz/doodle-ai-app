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
from create_doodle_video_v7_4_dark import DoodleVideoGeneratorV7_4_Dark

# --- CONFIGURATION ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
FAL_KEY = os.environ.get("FAL_KEY")
ELEVEN_LABS_KEY = os.environ.get("ELEVEN_LABS_API_KEY")

GROK_MODEL = "x-ai/grok-4.1-fast"
ELEVEN_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"

def log(msg):
    print(f"[TopicVideoV7.4] {msg}", flush=True)

def ensure_keys():
    if not all([OPENROUTER_API_KEY, FAL_KEY, ELEVEN_LABS_KEY]):
        log("❌ Missing API Keys (OpenRouter, Fal, or ElevenLabs)")
        sys.exit(1)

# --- 1. MANIFEST WITH PARTS ---

def generate_beat_manifest(topic):
    log(f"🧠 Generating V7.4 Manifest (with parts) for: {topic}...")
    
    prompt = f"""
    You are a whiteboard video script expert.
    Create a video script for: "{topic}".
    
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
    # solid -> Infographic (Colorful)
    # normal -> Black Ink Sketch
    # pencil -> Pencil Sketch
    # dark   -> Dark Mode (Black BG, White Ink)
    
    if style == "pencil":
        style_suffix = ", detailed graphite pencil sketch on white paper, gray lines, hand-drawn, artistic, shading, technical drawing style"
        negative_prompt = "color, ink, marker, heavy lines, solid black, photo, realistic, 3d, digital art"
        
    elif style == "dark":
        style_suffix = ", whiteboard style but with black background, white neon chalk lines, dark mode aesthetic, high contrast, clean white lines on black"
        negative_prompt = "white background, light mode, inverted, color, complex, filled, gradients, photo, realistic"

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
    parser.add_argument("--output_dir", default="topic_videos_v7_4", help="Output dir")
    parser.add_argument("--max_beats", type=int, default=0)
    # Styles: 'normal', 'solid', 'pencil', 'dark'
    parser.add_argument("--style", default="normal", choices=["normal", "solid", "pencil", "dark"], help="Image/Doodle style")
    args = parser.parse_args()

    ensure_keys()
    
    safe_topic = args.topic.lower().replace(" ", "_")
    work_dir = os.path.join(args.output_dir, safe_topic)
    os.makedirs(work_dir, exist_ok=True)
    
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
                generate_audio_part(p_script, p_audio_path)
            
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
        
        # E. Generate Doodle (V7.4 Dark)
        if not os.path.exists(final_beat_path):
            try:
                # Pass 'style' to generator
                gen = DoodleVideoGeneratorV7_4_Dark(
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
