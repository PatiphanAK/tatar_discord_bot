import discord
import asyncio
from typing import Dict, Optional
from ..models.music import Track, PlaybackState, PlaybackStatus
from ..services.youtube import YouTubeService
from ..services.voice_manager import VoiceManager
from ..utils.exceptions import PlaybackError
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class MusicPlayer:
    """Music playback management"""

    def __init__(
        self,
        voice_manager: VoiceManager,
        youtube_service: YouTubeService,
        ffmpeg_options: Dict[str, str]
    ):
        self.voice_manager = voice_manager
        self.youtube_service = youtube_service
        self.ffmpeg_options = ffmpeg_options
        self.playback_states: Dict[int, PlaybackState] = {}

    async def play(self, guild_id: int, url: str, requester_id: Optional[str] = None) -> Track:
        """Play music from URL"""
        try:
            # Check voice connection
            voice_client = self.voice_manager.get_voice_client(guild_id)
            if not voice_client or not voice_client.is_connected():
                raise PlaybackError("Not connected to voice channel")

            # Extract track information
            track = await self.youtube_service.extract_track_info(url, requester_id)

            # Stop current playback
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                await asyncio.sleep(0.1)

            # Create audio source
            audio_source = discord.FFmpegOpusAudio(track.url, **self.ffmpeg_options)

            # Setup playback callback
            def after_playing(error: Optional[Exception]):
                if error:
                    logger.error(f'Playback error: {error}')
                else:
                    logger.info(f'Finished playing {track.title}')

                # Update playback state
                if guild_id in self.playback_states:
                    self.playback_states[guild_id].status = PlaybackStatus.STOPPED

            # Start playing
            voice_client.play(audio_source, after=after_playing)

            # Update playback state
            self.playback_states[guild_id] = PlaybackState(
                status=PlaybackStatus.PLAYING,
                current_track=track,
                position=0
            )

            logger.info(f"Started playing '{track.title}' in guild {guild_id}")
            return track

        except Exception as e:
            logger.error(f"Playback error: {e}")
            raise PlaybackError(f"Failed to play music: {str(e)}")

    def stop(self, guild_id: int) -> bool:
        """Stop playback"""
        try:
            voice_client = self.voice_manager.get_voice_client(guild_id)
            if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
                voice_client.stop()
                self.playback_states[guild_id] = PlaybackState(status=PlaybackStatus.STOPPED)
                return True
            return False
        except Exception as e:
            logger.error(f"Stop error: {e}")
            return False

    def pause(self, guild_id: int) -> bool:
        """Pause playback"""
        try:
            voice_client = self.voice_manager.get_voice_client(guild_id)
            if voice_client and voice_client.is_playing():
                voice_client.pause()
                if guild_id in self.playback_states:
                    self.playback_states[guild_id].status = PlaybackStatus.PAUSED
                return True
            return False
        except Exception as e:
            logger.error(f"Pause error: {e}")
            return False

    def resume(self, guild_id: int) -> bool:
        """Resume playback"""
        try:
            voice_client = self.voice_manager.get_voice_client(guild_id)
            if voice_client and voice_client.is_paused():
                voice_client.resume()
                if guild_id in self.playback_states:
                    self.playback_states[guild_id].status = PlaybackStatus.PLAYING
                return True
            return False
        except Exception as e:
            logger.error(f"Resume error: {e}")
            return False

    def get_playback_state(self, guild_id: int) -> PlaybackState:
        """Get current playback state"""
        return self.playback_states.get(guild_id, PlaybackState())
