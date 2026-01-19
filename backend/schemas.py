from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    plan: Optional[str] = "free"
    video_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class VideoResponse(BaseModel):
    id: int
    title: str
    url: str
    r2_key: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class HistoryResponse(BaseModel):
    id: int
    query: str
    source_url: Optional[str] = None
    created_at: Optional[datetime] = None
    video: Optional[VideoResponse] = None

    class Config:
        from_attributes = True
