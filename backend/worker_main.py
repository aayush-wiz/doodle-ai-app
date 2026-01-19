import os
import asyncio
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Video, History, Base

# Ensure SOTA and parent modules are importable
sys.path.append(os.path.join(os.path.dirname(__file__), "SOTA"))
sys.path.append(os.path.dirname(__file__))

# Import SOTA generation logic
try:
    from SOTA.generate_topic_video_v7_4_text_corrected import process_video_request, get_voices
except ImportError:
    # Fallback for when SOTA is directly in path
    from generate_topic_video_v7_4_text_corrected import process_video_request, get_voices

from storage import upload_file_to_r2, get_public_url

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL not set")
    sys.exit(1)

from sqlalchemy.engine.url import make_url

# Parse and clean URL using SQLAlchemy utilities to avoid parsing errors
# Parse and clean URL using SQLAlchemy utilities to avoid parsing errors
try:
    url_obj = make_url(DATABASE_URL)
    
    # Switch driver if asyncpg
    if url_obj.drivername == "postgresql+asyncpg":
        url_obj = url_obj._replace(drivername="postgresql")
    
    # Handle query parameters
    current_query = dict(url_obj.query)
    
    # Remove 'ssl' (invalid for psycopg2)
    if "ssl" in current_query:
        del current_query["ssl"]
        
    # Ensure sslmode=require (needed for Neon)
    current_query["sslmode"] = "require"
    
    # Update URL object with new query params
    url_obj = url_obj._replace(query=current_query)
    
    print(f"DEBUG: DB URL Host: {url_obj.host}, Port: {url_obj.port}, User: {url_obj.username}, Password Length: {len(url_obj.password) if url_obj.password else 0}")
    
    # Create engine directly with URL object to avoid string encoding issues
    engine = create_engine(url_obj)
    
except Exception as e:
    print(f"Error preparing database URL object: {e}. Falling back to basic string replace.")
    # Fallback just in case
    SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    if "?" in SYNC_DATABASE_URL:
        if "sslmode" not in SYNC_DATABASE_URL:
             SYNC_DATABASE_URL += "&sslmode=require"
    else:
        SYNC_DATABASE_URL += "?sslmode=require"
    
    print(f"DEBUG: Using Fallback String URL Host: {make_url(SYNC_DATABASE_URL).host}")
    engine = create_engine(SYNC_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def config_env():
    # Ensure keys are stripped
    keys_to_strip = ["R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME", 
                     "OPENAI_API_KEY", "ELEVEN_LABS_API_KEY", "FAL_KEY"]
    for key in keys_to_strip:
        val = os.environ.get(key)
        if val:
            os.environ[key] = val.strip()

def run_worker():
    config_env()
    
    # Read inputs from Env
    topic = os.getenv("VIDEO_TOPIC")
    style = os.getenv("VIDEO_STYLE", "normal")
    voice = os.getenv("VIDEO_VOICE")
    language = os.getenv("VIDEO_LANGUAGE", "en")
    max_beats = int(os.getenv("VIDEO_MAX_BEATS", "0"))
    user_id = os.getenv("USER_ID")
    
    if not topic or not user_id:
        print("Error: VIDEO_TOPIC and USER_ID are required")
        sys.exit(1)
        
    print(f"Starting Worker for Topic: {topic}, User: {user_id}")
    
    # Voice resolution
    voice_to_use = voice
    if voice:
        print(f"Resolving voice: '{voice}'")
        try:
            voices = get_voices()
            print(f"Available voices keys: {list(voices.keys())}")
            
            if voice in voices:
                voice_to_use = voices[voice]
                print(f"Resolved voice '{voice}' to ID: {voice_to_use}")
            else:
                print(f"WARNING: Voice '{voice}' not found in available voices!")
                # Try partial match or case insensitive match?
                for v_name, v_id in voices.items():
                    if voice.lower() in v_name.lower():
                        print(f"Found fuzzy match: '{v_name}' -> {v_id}")
                        voice_to_use = v_id
                        break
        except Exception as e:
            print(f"Error fetching voices for resolution: {e}")
            
    # Generate Video
    try:
        video_path = process_video_request(
            topic,
            style,
            voice_to_use,
            language,
            max_beats
        )
    except Exception as e:
        print(f"Error during video generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    if not video_path or not os.path.exists(video_path):
        print("Error: Video generation returned no path or file missing")
        sys.exit(1)
        
    print(f"Video generated at: {video_path}")
    
    # Upload to R2
    filename = os.path.basename(video_path)
    r2_key = upload_file_to_r2(video_path, filename)
    
    if not r2_key:
        print("Error: R2 Upload failed")
        sys.exit(1)
        
    final_url = get_public_url(r2_key)
    print(f"Uploaded to R2: {final_url}")
    
    # DB Update
    try:
        db = SessionLocal()
        
        # Create Video Record
        new_video = Video(
            title=topic,
            r2_key=r2_key,
            url=final_url,
            user_id=int(user_id)
        )
        db.add(new_video)
        db.commit()
        db.refresh(new_video)
        
        # Create History Record
        new_history = History(
            user_id=int(user_id),
            query=topic,
            video_id=new_video.id
        )
        db.add(new_history)
        db.commit()
        
        print(f"DB Updated. Video ID: {new_video.id}")
        db.close()
        
    except Exception as e:
        print(f"Error updating DB: {e}")
        sys.exit(1)
        
    # Cleanup
    try:
        os.remove(video_path)
        print("Local file cleaned up")
    except:
        pass
        
    print("SUCCESS")

if __name__ == "__main__":
    run_worker()
