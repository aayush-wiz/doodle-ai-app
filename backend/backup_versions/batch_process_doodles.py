import os
import glob
import sys

# Add current dir to path to import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from create_doodle_video import DoodleVideoGenerator

TARGET_DIR = "/Users/hritvik/Downloads/learning-software-book (2)/public/images/course-k-nearest-neighbors"
images = glob.glob(os.path.join(TARGET_DIR, "*.png"))

print(f"Found {len(images)} images in {TARGET_DIR}")

for i, img_path in enumerate(images):
    base_name = os.path.splitext(img_path)[0]
    output_path = base_name + "_doodle.mp4"
    
    # Skip if already exists? No, user asked to recreate.
    
    print(f"[{i+1}/{len(images)}] Processing {os.path.basename(img_path)}...")
    try:
        # Using 4 seconds per video for quick turnaround, unless user wants specific syncing. 
        # Since I don't have audio files here, I'll use a fixed duration.
        gen = DoodleVideoGenerator(img_path, output_path, duration=4.0)
        gen.generate()
    except Exception as e:
        print(f"❌ Failed {img_path}: {e}")

print("✨ All done!")
