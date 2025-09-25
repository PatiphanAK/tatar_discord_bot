import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class PlayRequest(BaseModel):
    guild_id: int
    channel_id: int
    url: str
    user_id: Optional[str] = None

class ControlRequest(BaseModel):
    guild_id: int

def create_music_routes(music_bot):
    """Create music API routes with thread-safe execution"""
    router = APIRouter()

    def execute_in_bot_loop(coro):
        """Execute coroutine in bot's event loop thread-safely"""
        try:
            # Wait for bot to be ready and loop to be available
            max_wait = 30  # 30 seconds max wait
            wait_count = 0

            while not hasattr(music_bot, '_bot_loop') or music_bot._bot_loop is None:
                if wait_count >= max_wait * 10:  # 100ms intervals
                    raise HTTPException(
                        status_code=503,
                        detail="Bot not ready - no event loop available"
                    )
                import time
                time.sleep(0.1)
                wait_count += 1

            # Execute in bot's event loop
            future = asyncio.run_coroutine_threadsafe(coro, music_bot._bot_loop)
            return future.result(timeout=30)

        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Request timeout")
        except Exception as e:
            logger.error(f"Error executing in bot loop: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/play")
    async def play_music(request: PlayRequest):
        """Play music"""
        try:
            logger.info(f"Play request: {request.dict()}")

            # Execute in bot's event loop
            track = execute_in_bot_loop(
                music_bot.play_music(
                    request.guild_id,
                    request.channel_id,
                    request.url,
                    request.user_id
                )
            )

            logger.info(f"Successfully started playing: {track.title}")

            # Return JSON response for Go client
            return {
                "success": True,
                "title": track.title,
                "error": ""
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Play error: {e}")
            return {
                "success": False,
                "title": "",
                "error": f"Failed to play music: {str(e)}"
            }

    @router.post("/stop")
    async def stop_music(request: ControlRequest):
        """Stop music"""
        try:
            logger.info(f"Stop request: guild_id={request.guild_id}")

            # Get current track info before stopping
            status = music_bot.get_status(request.guild_id)
            current_track = status.get("playback_state", {}).get("current_track")
            track_title = current_track.get("title", "Unknown") if current_track else "No track"

            stopped = execute_in_bot_loop(
                music_bot.stop_music(request.guild_id)
            )

            if stopped:
                return {
                    "success": True,
                    "title": f"Stopped: {track_title}",
                    "error": ""
                }
            else:
                return {
                    "success": False,
                    "title": "",
                    "error": "No music was playing"
                }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Stop error: {e}")
            return {
                "success": False,
                "title": "",
                "error": f"Failed to stop music: {str(e)}"
            }

    @router.post("/pause")
    async def pause_music(request: ControlRequest):
        """Pause music"""
        try:
            logger.info(f"Pause request: guild_id={request.guild_id}")

            # Get current track info
            status = music_bot.get_status(request.guild_id)
            current_track = status.get("playback_state", {}).get("current_track")
            track_title = current_track.get("title", "Unknown") if current_track else "No track"

            paused = execute_in_bot_loop(
                music_bot.pause_music(request.guild_id)
            )

            if paused:
                return f"Paused: {track_title}"
            else:
                return "No music to pause"

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Pause error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to pause music: {str(e)}")

    @router.post("/resume")
    async def resume_music(request: ControlRequest):
        """Resume music"""
        try:
            logger.info(f"Resume request: guild_id={request.guild_id}")

            # Get current track info
            status = music_bot.get_status(request.guild_id)
            current_track = status.get("playback_state", {}).get("current_track")
            track_title = current_track.get("title", "Unknown") if current_track else "No track"

            resumed = execute_in_bot_loop(
                music_bot.resume_music(request.guild_id)
            )

            if resumed:
                return f"Resumed: {track_title}"
            else:
                return "No paused music to resume"

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Resume error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to resume music: {str(e)}")

    @router.post("/leave")
    async def leave_channel(request: ControlRequest):
        """Leave voice channel"""
        try:
            logger.info(f"Leave request: guild_id={request.guild_id}")

            left = execute_in_bot_loop(
                music_bot.leave_channel(request.guild_id)
            )

            if left:
                return "Left voice channel"
            else:
                return "Not connected to voice channel"

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Leave error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to leave channel: {str(e)}")

    @router.get("/status/{guild_id}")
    async def get_status(guild_id: int):
        """Get bot status with current playing track"""
        try:
            logger.info(f"Status request: guild_id={guild_id}")

            # This method doesn't use async Discord operations
            status = music_bot.get_status(guild_id)

            # Add more detailed current track info
            if status.get("playback_state", {}).get("current_track"):
                current_track = status["playback_state"]["current_track"]
                status["now_playing"] = {
                    "title": current_track.get("title", "Unknown"),
                    "uploader": current_track.get("uploader", "Unknown"),
                    "duration": current_track.get("duration", 0),
                    "formatted_duration": format_duration(current_track.get("duration", 0))
                }
            else:
                status["now_playing"] = None

            return status

        except Exception as e:
            logger.error(f"Status error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

    def format_duration(seconds):
        """Format duration in seconds to MM:SS"""
        if not seconds:
            return "00:00"

        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    @router.get("/now-playing/{guild_id}")
    async def now_playing(guild_id: int):
        """Get currently playing track information"""
        try:
            status = music_bot.get_status(guild_id)
            playback_state = status.get("playback_state", {})
            current_track = playback_state.get("current_track")

            if not current_track:
                return {
                    "playing": False,
                    "message": "No music currently playing"
                }

            return {
                "playing": True,
                "status": playback_state.get("status", "unknown"),
                "track": {
                    "title": current_track.get("title", "Unknown"),
                    "uploader": current_track.get("uploader", "Unknown"),
                    "duration": current_track.get("duration", 0),
                    "formatted_duration": format_duration(current_track.get("duration", 0)),
                    "requester_id": current_track.get("requester_id")
                },
                "message": f"Now playing: {current_track.get('title', 'Unknown')}"
            }

        except Exception as e:
            logger.error(f"Now playing error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get current track: {str(e)}")

    @router.get("/health")
    async def health_check():
        """Health check endpoint"""
        bot_ready = hasattr(music_bot, '_bot_loop') and music_bot._bot_loop is not None
        return {
            "status": "healthy",
            "bot_ready": bot_ready,
            "bot_user": str(music_bot.user) if music_bot.user else None
        }

    return router
