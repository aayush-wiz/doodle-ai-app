"""
Upload category videos to R2 storage.
This script finds all final videos and uploads them to R2 with clean names.
"""
import os
import json
from pathlib import Path
from storage import upload_file_to_r2, get_r2_client, R2_ACCOUNT_ID, R2_BUCKET_NAME

# Video directories to scan
VIDEO_DIRS = [
    "topic_videos_v7_4",
    "tested_videos/topic_videos_v7_2",
    "tested_videos/topic_videos_v7_1",
]

# Mapping of video topics to display info
VIDEO_METADATA = {
    "how_black_holes_are_formed": {
        "title": "How Black Holes Are Formed",
        "category": "Science",
        "author": "Cosmos Academy",
        "views": "2.3M",
        "duration": "01:45"
    },
    "how_black_holes_form?": {
        "title": "How Black Holes Form",
        "category": "Science", 
        "author": "Space Explorers",
        "views": "1.8M",
        "duration": "01:30"
    },
    "how_linear_regression_works?": {
        "title": "How Linear Regression Works",
        "category": "Math",
        "author": "ML Academy",
        "views": "890K",
        "duration": "02:15"
    },
    "how_stock_market_works_in_new_york_and_london_tech_centers": {
        "title": "How the Stock Market Works",
        "category": "Technology",
        "author": "Finance Hub",
        "views": "1.5M",
        "duration": "03:00"
    },
    "how_the_human_dna_evolves": {
        "title": "How Human DNA Evolves",
        "category": "Science",
        "author": "Biology Channel",
        "views": "1.1M",
        "duration": "01:50"
    },
    "how_the_human_evolution_works": {
        "title": "How Human Evolution Works",
        "category": "Science",
        "author": "Evolution Studies",
        "views": "2.0M",
        "duration": "02:00"
    },
    "special_theory_of_relativity": {
        "title": "Special Theory of Relativity",
        "category": "Science",
        "author": "Physics Pro",
        "views": "3.2M",
        "duration": "02:30"
    },
    "what_is_encoder_decoder_transformer_architecture_and_how_it_works?_bb5a73c5": {
        "title": "Transformer Architecture Explained",
        "category": "Technology",
        "author": "AI Insights",
        "views": "950K",
        "duration": "02:45"
    },
    "lstm_with_self_attention": {
        "title": "LSTM with Self Attention",
        "category": "Technology",
        "author": "Deep Learning Lab",
        "views": "720K",
        "duration": "02:10"
    },
    "combustion_engine": {
        "title": "How a Combustion Engine Works",
        "category": "Technology",
        "author": "Engineering World",
        "views": "1.4M",
        "duration": "01:55"
    }
}


def find_final_videos(base_dir: str) -> list:
    """Find all final video files (not beat files)."""
    videos = []
    base_path = Path(base_dir)
    
    for video_dir in VIDEO_DIRS:
        dir_path = base_path / video_dir
        if not dir_path.exists():
            print(f"Directory not found: {dir_path}")
            continue
            
        for topic_dir in dir_path.iterdir():
            if not topic_dir.is_dir():
                continue
                
            topic_name = topic_dir.name
            
            # Find the final video file (not beat_* files)
            for video_file in topic_dir.glob("*.mp4"):
                if not video_file.name.startswith("beat_"):
                    videos.append({
                        "path": str(video_file),
                        "topic": topic_name,
                        "filename": video_file.name
                    })
                    break  # Only take the first final video
    
    return videos


def upload_videos():
    """Upload all videos to R2 and return the mapping."""
    client = get_r2_client()
    if not client:
        print("Failed to get R2 client. Check your credentials.")
        return []
    
    base_dir = Path(__file__).parent
    videos = find_final_videos(base_dir)
    
    print(f"Found {len(videos)} videos to upload")
    
    results = []
    
    for i, video in enumerate(videos, 1):
        topic = video["topic"]
        file_path = video["path"]
        
        # Create clean object key
        clean_name = topic.replace("?", "").replace(" ", "_").lower()
        # Remove hash suffixes like _bb5a73c5
        if "_" in clean_name and len(clean_name.split("_")[-1]) == 8:
            parts = clean_name.rsplit("_", 1)
            if all(c in "0123456789abcdef" for c in parts[-1]):
                clean_name = parts[0]
        
        object_key = f"category/{clean_name}.mp4"
        
        print(f"[{i}/{len(videos)}] Uploading: {topic}")
        print(f"  File: {video['filename']}")
        print(f"  Key: {object_key}")
        
        # Upload to R2
        result = upload_file_to_r2(file_path, object_key)
        
        if result:
            # Construct public URL (assuming public bucket with r2.dev domain)
            public_url = f"https://pub-{R2_ACCOUNT_ID}.r2.dev/{object_key}"
            
            # Get metadata
            meta = VIDEO_METADATA.get(topic, {
                "title": topic.replace("_", " ").title(),
                "category": "Science",
                "author": "chytr Studio",
                "views": "0",
                "duration": "00:00"
            })
            
            results.append({
                "id": i,
                "title": meta["title"],
                "author": meta["author"],
                "views": meta["views"],
                "duration": meta["duration"],
                "category": meta["category"],
                "url": public_url,
                "object_key": object_key,
                "image": f"https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800&auto=format&fit=crop"  # Placeholder
            })
            print(f"  ✓ Uploaded successfully")
        else:
            print(f"  ✗ Upload failed")
    
    return results


def main():
    print("=" * 60)
    print("Category Videos Upload to R2")
    print("=" * 60)
    
    results = upload_videos()
    
    print("\n" + "=" * 60)
    print(f"Upload complete! {len(results)} videos uploaded.")
    print("=" * 60)
    
    # Save results to JSON
    output_file = Path(__file__).parent / "category_videos.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Print TypeScript array for frontend
    print("\n" + "=" * 60)
    print("TypeScript array for DashboardSection.tsx:")
    print("=" * 60)
    print("\nconst TRENDING_VIDEOS: VideoItem[] = [")
    for video in results:
        print(f"""    {{
        id: {video['id']},
        title: "{video['title']}",
        author: "{video['author']}",
        views: "{video['views']}",
        duration: "{video['duration']}",
        image: "{video['image']}",
        category: "{video['category']}",
        url: "{video['url']}"
    }},""")
    print("];")


if __name__ == "__main__":
    main()
