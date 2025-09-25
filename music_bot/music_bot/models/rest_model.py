from pydantic import BaseModel
from typing import Optional
from .music import Track, VoiceConnection, PlaybackState

class PlayRequest(BaseModel):
    """Play music request model"""
    guild_id: str
    channel_id: str
    url: str
    user_id: str

class StopRequest(BaseModel):
    """Stop music request model"""
    guild_id: str

class PlayResponse(BaseModel):
    """Play music response model"""
    success: bool
    message: str
    track: Optional[Track] = None
    error: Optional[str] = None

class StatusResponse(BaseModel):
    """Status response model"""
    connected: bool
    playback_state: PlaybackState
    voice_connection: Optional[VoiceConnection] = None

class OperationResponse(BaseModel):
    """Generic operation response"""
    success: bool
    message: str
    error: Optional[str] = None
