import os
import sys
import asyncio
from typing import Optional, List
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, Depends, status, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.future import select

# Imports for Auth and DB
from database import engine, Base, get_db
from models import User, Video, History
from schemas import UserCreate, UserResponse, Token, TokenData, VideoResponse, HistoryResponse
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from storage import upload_file_to_r2, create_presigned_url, get_public_url
from datetime import timedelta
from pydantic import BaseModel

# Add SOTA directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "SOTA"))


# Import voices separately - lightweight, no moviepy dependency
from voices import get_voices

# SOTA module for video generation (has heavy dependencies)
try:
    from SOTA.generate_topic_video_v7_4_text_corrected import process_video_request
except ImportError:
    try:
        from generate_topic_video_v7_4_text_corrected import process_video_request
    except ImportError as e:
        print(f"Error importing SOTA modules: {e}")
        # Fallback for when SOTA isn't available (but voices still work)
        def process_video_request(*args, **kwargs): raise NotImplementedError("SOTA module not loaded")

app = FastAPI(title="Doodle AI API")

# CORS - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Serve generated videos statically (local fallback)
OUTPUT_DIR = os.path.join(os.getcwd(), "SOTA", "topic_videos_v7_4")
# Note: The original code had OUTPUT_DIR = os.path.join(os.getcwd(), "topic_videos_v7_4") 
# but SOTA script usually writes relative to its dir. 
# Let's ensure we point to where the script writes. 
# Based on file listing earlier, 'topic_videos_v7_4' is in 'backend'.
# So we stick to backend/topic_videos_v7_4
OUTPUT_DIR = os.path.join(os.getcwd(), "topic_videos_v7_4")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

app.mount("/local_videos", StaticFiles(directory=OUTPUT_DIR), name="local_videos")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# --- Auth Routes ---

@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    async with db as session:
        result = await session.execute(select(User).where(User.username == user.username))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        hashed_password = get_password_hash(user.password)
        db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: UserCreate, db: Session = Depends(get_db)):
    # Note: Usually OAuth2PasswordRequestForm is used, but reusing UserCreate for simplicity/JSON support
    # Or strict adherence to form data. Let's support JSON via UserCreate for now as it's easier for frontend 
    # unless we want standard OAuth2 form encoding.
    # To keep it standard with existing tools, I'll accept JSON body 'UserCreate' effectively.
    # But usually /token expects form data. 
    # Let's stick to the Pydantic model 'UserCreate' as the body:
    
    async with db as session:
        result = await session.execute(select(User).where(User.username == form_data.username))
        user = result.scalars().first()
        
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# --- Video Routes ---

class VideoRequest(BaseModel):
    topic: str
    style: str = "normal"
    voice: Optional[str] = None
    language: Optional[str] = "en"
    max_beats: int = 0
    user_id: int

@app.get("/voices")
def list_voices():
    """Get available ElevenLabs voices"""
    voices = get_voices()
    return {"voices": voices}

@app.websocket("/ws/generate")
async def websocket_generate(websocket: WebSocket):
    await websocket.accept()
    
    import httpx
    # Import locally to avoid circulars or heavy loads at top level if desired, 
    # matching original function style
    from database import SessionLocal
    from sqlalchemy import update

    try:
        # 1. Receive Initial Config
        data = await websocket.receive_json()
        print(f"WS Received: {data}")
        
        # Parse into VideoRequest-like object or dict
        # Expecting: { topic, style, voice, language, max_beats, user_id, token? }
        
        topic = data.get("topic", "").strip()
        user_id = data.get("user_id")
        style = data.get("style", "normal")
        voice = data.get("voice", "")
        language = data.get("language", "en")
        max_beats = int(data.get("max_beats", 0))

        if not topic or not user_id:
            await websocket.send_json({"status": "error", "detail": "Missing topic or user_id"})
            await websocket.close()
            return

        # 2. Verify User & Limits
        async with SessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            current_user = result.scalars().first()
            if not current_user:
                 await websocket.send_json({"status": "error", "detail": "User not found"})
                 await websocket.close()
                 return
            
            user_plan = current_user.plan or "free"
            user_video_count = current_user.video_count or 0

            if user_plan == "free" and user_video_count >= 3:
                await websocket.send_json({"status": "error", "detail": "Free tier limit reached."})
                await websocket.close()
                return

        # 3. Notify: Starting
        await websocket.send_json({"status": "processing", "message": "Spawning worker..."})

        # 4. Spawn Fly Machine
        FLY_API_TOKEN = os.getenv("FLY_API_TOKEN")
        FLY_APP_NAME = "doodle-ai-worker-gen"
        
        if not FLY_API_TOKEN:
            await websocket.send_json({"status": "error", "detail": "Server config error (FLY_TOKEN)."})
            await websocket.close()
            return

        env_vars = {
            "VIDEO_TOPIC": topic,
            "VIDEO_STYLE": style,
            "VIDEO_VOICE": voice,
            "VIDEO_LANGUAGE": language,
            "VIDEO_MAX_BEATS": str(max_beats),
            "USER_ID": str(user_id),
            "DATABASE_URL": os.getenv("DATABASE_URL", "")
        }
        
        keys_to_pass = ["R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME", "R2_PUBLIC_URL",
                        "OPENAI_API_KEY", "ELEVEN_LABS_API_KEY", "FAL_KEY"]
        for key in keys_to_pass:
            val = os.getenv(key)
            if val:
                env_vars[key] = val

        machine_config = {
            "config": {
            "image": os.getenv("WORKER_IMAGE", "registry.fly.io/doodle-ai-worker-gen:deployment-01KEJVS1GFW9D2RKX1XWG7DA1E"),
                "guest": {
                    "cpu_kind": "performance",
                    "cpus": 1,
                    "memory_mb": 8192
                },
                "auto_destroy": True,
                "restart": {"policy": "no"},
                "env": env_vars,
            }
        }

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {FLY_API_TOKEN}"}
            resp = await client.post(
                f"https://api.machines.dev/v1/apps/{FLY_APP_NAME}/machines",
                json=machine_config,
                headers=headers
            )
            
            if resp.status_code != 200:
                await websocket.send_json({"status": "error", "detail": f"Failed to spawn: {resp.text}"})
                await websocket.close()
                return
            
            machine_data = resp.json()
            machine_id = machine_data['id']
            await websocket.send_json({"status": "processing", "message": "Worker started. Generating..."})

            # 5. Poll for Completion
            max_retries = 120 # 10 minutes max? (120 * 5s = 600s)
            found_machine = True
            
            for _ in range(max_retries):
                await asyncio.sleep(5)
                
                # Retrieve Machine Status
                status_resp = await client.get(
                    f"https://api.machines.dev/v1/apps/{FLY_APP_NAME}/machines/{machine_id}",
                    headers=headers
                )
                
                if status_resp.status_code == 404:
                    print(f"Machine {machine_id} gone, checking DB result...")
                    break # Machine destroyed, hopefully finished
                
                if status_resp.status_code == 200:
                    info = status_resp.json()
                    state = info.get("state")
                    if state in ["stopped", "destroyed"]:
                        print(f"Machine {machine_id} stopped.")
                        break
                    # Optional: Could fetch logs here if Fly allows simple log check via API??
                    # For now, just keep "processing"
                    # await websocket.send_json({"status": "processing", "message": "Still dreaming..."})

            # 6. Fetch Result from DB
            await asyncio.sleep(2) # DB sync buffer
            async with SessionLocal() as db:
                 result = await db.execute(
                     select(Video)
                     .where(Video.user_id == user_id)
                     .where(Video.title == topic)
                     .order_by(Video.created_at.desc())
                     .limit(1)
                 )
                 new_video = result.scalars().first()
                 
                 if new_video:
                     # Store values before commit expires the object
                     video_url = new_video.url
                     r2_key = new_video.r2_key
                     video_id = new_video.id
                     
                     # Update usage
                     await db.execute(
                         update(User)
                         .where(User.id == user_id)
                         .values(video_count=User.video_count + 1)
                     )
                     await db.commit()
                     
                     await websocket.send_json({
                        "status": "success",
                        "video_path": "remote",
                        "video_url": video_url,
                        "r2_key": r2_key,
                        "id": video_id
                     })
                 else:
                     await websocket.send_json({"status": "error", "detail": "Video generation failed (no DB record)."})
            
            await websocket.close()

    except WebSocketDisconnect:
        print("WS Client Disconnected")
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({"status": "error", "detail": str(e)})
            await websocket.close()
        except:
            pass  


@app.get("/videos", response_model=List[VideoResponse])
async def get_my_videos(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    async with db as session:
        result = await session.execute(select(Video).where(Video.user_id == current_user.id).order_by(Video.created_at.desc()))
        videos = result.scalars().all()
        return videos

@app.get("/history", response_model=List[HistoryResponse])
async def get_my_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    async with db as session:
        # Eager load video for history
        from sqlalchemy.orm import selectinload
        result = await session.execute(
            select(History)
            .where(History.user_id == current_user.id)
            .order_by(History.created_at.desc())
            .options(selectinload(History.video))
        )
        history = result.scalars().all()
        return history

@app.get("/videos/{r2_key:path}")
async def get_video(r2_key: str):
    """Redirect to signed R2 URL"""
    url = create_presigned_url(r2_key)
    if not url:
        raise HTTPException(status_code=404, detail="Video not found or storage inaccessible")
    return RedirectResponse(url)

@app.get("/health")
def health():
    return {"status": "ok"}
