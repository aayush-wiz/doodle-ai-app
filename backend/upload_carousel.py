import os
import sys
from storage import upload_file_to_r2, get_public_url

# Define files to upload
FILES = [
    "/Users/hritvik/doodle-ai/backend/topic_videos_v7_4/crousel1.mp4",
    "/Users/hritvik/doodle-ai/backend/topic_videos_v7_4/coursel2.mp4", # Typo matches user request
    "/Users/hritvik/doodle-ai/backend/topic_videos_v7_4/crousel3.mp4"
]

def main():
    print("Starting upload...")
    for file_path in FILES:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
            
        filename = os.path.basename(file_path)
        # Fix typo in filename if needed, but let's keep original names for now as requested
        # Actually user might prefer clean names
        # User said "add these 3 videos...". I'll keep names but ensure uniqueness if needed.
        
        print(f"Uploading {filename}...")
        key = upload_file_to_r2(file_path)
        
        if key:
            url = get_public_url(key)
            print(f"SUCCESS: {filename} -> {url}")
        else:
            print(f"FAILED: {filename}")

if __name__ == "__main__":
    main()
