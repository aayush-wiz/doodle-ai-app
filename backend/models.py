from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True) # Optional, usually email is enough but added for flexibility
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    plan = Column(String, default="free")
    video_count = Column(Integer, default=0)

    videos = relationship("Video", back_populates="owner")

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    r2_key = Column(String, index=True) # Key in R2 bucket
    url = Column(String) # Public or presigned URL
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="videos")
    history_entries = relationship("History", back_populates="video")

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query = Column(Text) # The user prompt/request
    source_url = Column(String, nullable=True) # Optional context URL
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="history")
    video = relationship("Video", back_populates="history_entries")

# Update User to include history relationship
User.history = relationship("History", back_populates="user")
