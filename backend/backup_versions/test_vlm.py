
import os
import requests
import base64
import json
import traceback
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_vlm():
    print("Testing VLM Connectivity...")
    
    # 1. Check for an image to test with
    test_img = "test_image.png"
    # Create a dummy image if not exists, or try to find one in the folder
    # Let's look for one in topic_videos_v6
    
    found_img = None
    for root, dirs, files in os.walk("topic_videos_v6"):
        for f in files:
            if f.endswith(".png"):
                found_img = os.path.join(root, f)
                break
        if found_img: break
    
    if not found_img:
        print("❌ No test image found in topic_videos_v6/. Please run the generator once or provide an image.")
        return

    print(f"📸 Using image: {found_img}")
    base64_img = encode_image(found_img)
    
    # 2. Call VLM
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://learning-software.local",
    }
    
    prompt = """
    Locate the main elements in this diagram.
    Return a JSON dict where keys are "1", "2", "3" and values are [ymin, xmin, ymax, xmax] (0-1000).
    """
    
    model = "openai/gpt-4o"
    print(f"🤖 Model: {model}")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                ]
            }
        ],
        "response_format": {"type": "json_object"}
    }
    
    try:
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
        print(f"📡 Status Code: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ Error Body: {resp.text}")
            return
            
        content = resp.json()['choices'][0]['message']['content']
        print(f"📝 Raw Content: {content}")
        
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    test_vlm()
