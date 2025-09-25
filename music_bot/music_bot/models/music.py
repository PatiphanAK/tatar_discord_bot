from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class PlaybackStatus(str, Enum):
    """Playback status enumeration"""
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"

class Track(BaseModel):
    """Track information model"""
    title: str = Field(..., description="Track title")
    url: str = Field(..., description="Original URL")
    duration: int = Field(0, ge=0, description="Duration in seconds")
    uploader: str = Field("Unknown", description="Content uploader")
    track_id: str = Field(..., description="Unique track identifier")
    requester_id: Optional[str] = Field(None, description="User ID who requested")

class PlaybackState(BaseModel):
    """Current playback state"""
    status: PlaybackStatus = PlaybackStatus.STOPPED
    current_track: Optional[Track] = None
    position: int = Field(0, ge=0, description="Current position in seconds")
    volume: float = Field(0.25, ge=0.0, le=1.0, description="Volume level")

class VoiceConnection(BaseModel):
    """Voice connection information"""
    guild_id: int
    channel_id: int
    channel_name: str
    connected: bool = True
