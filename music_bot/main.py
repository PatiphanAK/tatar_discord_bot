import discord
from discord.ext import commands
import asyncio
import yt_dlp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import threading
from typing import Optional, Dict
import logging
import os
from dotenv import load_dotenv
from concurrent.futures import Future
import functools

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Discord Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")

# Global variable to store bot's event loop
bot_loop = None

# Simplified YDL Options (similar to working code)
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
}

# Simplified FFMPEG Options (using Opus like working code)
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -filter:a "volume=0.25"'
}

# Pydantic Models for API
class MusicRequest(BaseModel):
    guild_id: str
    channel_id: str
    url: str
    user_id: str

class StopRequest(BaseModel):
    guild_id: str

class MusicResponse(BaseModel):
    success: bool
    message: str
    title: str = ""
    track_id: str = ""
    error: str = ""

class StatusResponse(BaseModel):
    playing: bool
    track: str = ""
    duration: int = 0
    position: int = 0
    queue_length: int = 0

class MusicBot:
    def __init__(self):
        self.voice_clients: Dict[int, discord.VoiceClient] = {}
        self.current_track: Dict[int, dict] = {}
        self.is_playing: Dict[int, bool] = {}
        self.is_paused: Dict[int, bool] = {}
        self.ytdl = yt_dlp.YoutubeDL(YDL_OPTIONS)

    async def join_voice_channel(self, channel_id: int, guild_id: int) -> bool:
        """Join a voice channel - thread-safe version"""
        try:
            # Run in bot's event loop if called from different thread
            if asyncio.get_event_loop() != bot_loop:
                future = asyncio.run_coroutine_threadsafe(
                    self._join_voice_channel_internal(channel_id, guild_id),
                    bot_loop
                )
                return future.result(timeout=30)  # 30 second timeout
            else:
                return await self._join_voice_channel_internal(channel_id, guild_id)
        except Exception as e:
            logger.error(f"Failed to join voice channel: {e}")
            return False

    async def _join_voice_channel_internal(self, channel_id: int, guild_id: int) -> bool:
        """Internal method that must run in bot's event loop"""
        try:
            channel = bot.get_channel(channel_id)
            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return False

            # Disconnect if already connected
            if guild_id in self.voice_clients:
                await self.voice_clients[guild_id].disconnect()

            voice_client = await channel.connect()
            self.voice_clients[guild_id] = voice_client
            logger.info(f"Connected to voice channel {channel_id} in guild {guild_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to join voice channel internal: {e}")
            return False

    async def play_music(self, guild_id: int, url: str) -> dict:
        """Play music from URL - thread-safe version"""
        try:
            # Run in bot's event loop if called from different thread
            if asyncio.get_event_loop() != bot_loop:
                future = asyncio.run_coroutine_threadsafe(
                    self._play_music_internal(guild_id, url),
                    bot_loop
                )
                return future.result(timeout=60)  # 60 second timeout for download
            else:
                return await self._play_music_internal(guild_id, url)
        except Exception as e:
            logger.error(f"Failed to play music: {e}")
            return {"success": False, "error": str(e)}

    async def _play_music_internal(self, guild_id: int, url: str) -> dict:
        """Internal method that must run in bot's event loop"""
        try:
            if guild_id not in self.voice_clients:
                return {"success": False, "error": "Bot not connected to voice channel"}

            voice_client = self.voice_clients[guild_id]

            # Extract audio info (run in executor like working code)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))

            song_url = data['url']
            title = data.get('title', 'Unknown')
            duration = data.get('duration', 0)

            # Create audio source (using FFmpegOpusAudio like working code)
            player = discord.FFmpegOpusAudio(song_url, **FFMPEG_OPTIONS)

            # Stop current playback if playing
            if voice_client.is_playing():
                voice_client.stop()

            # Start playing (simplified - no complex callback)
            voice_client.play(player)

            # Update status
            self.current_track[guild_id] = {
                "title": title,
                "url": url,
                "duration": duration
            }
            self.is_playing[guild_id] = True
            self.is_paused[guild_id] = False

            logger.info(f"Started playing {title} in guild {guild_id}")

            return {
                "success": True,
                "message": f"Now playing: {title}",
                "title": title,
                "track_id": str(hash(url))
            }

        except Exception as e:
            logger.error(f"Failed to play music internal: {e}")
            return {"success": False, "error": str(e)}

    async def stop_music(self, guild_id: int) -> dict:
        """Stop music playback"""
        try:
            if guild_id not in self.voice_clients:
                return {"success": False, "error": "Bot not connected to voice channel"}

            voice_client = self.voice_clients[guild_id]
            voice_client.stop()

            self.is_playing[guild_id] = False
            self.is_paused[guild_id] = False

            return {"success": True, "message": "Stopped playback"}

        except Exception as e:
            logger.error(f"Failed to stop music: {e}")
            return {"success": False, "error": str(e)}

    async def pause_music(self, guild_id: int) -> dict:
        """Pause music playback"""
        try:
            if guild_id not in self.voice_clients:
                return {"success": False, "error": "Bot not connected to voice channel"}

            voice_client = self.voice_clients[guild_id]
            if voice_client.is_playing():
                voice_client.pause()
                self.is_paused[guild_id] = True
                return {"success": True, "message": "Paused playback"}
            else:
                return {"success": False, "error": "Nothing is playing"}

        except Exception as e:
            logger.error(f"Failed to pause music: {e}")
            return {"success": False, "error": str(e)}

    async def resume_music(self, guild_id: int) -> dict:
        """Resume music playback"""
        try:
            if guild_id not in self.voice_clients:
                return {"success": False, "error": "Bot not connected to voice channel"}

            voice_client = self.voice_clients[guild_id]
            if voice_client.is_paused():
                voice_client.resume()
                self.is_paused[guild_id] = False
                return {"success": True, "message": "Resumed playback"}
            else:
                return {"success": False, "error": "Music is not paused"}

        except Exception as e:
            logger.error(f"Failed to resume music: {e}")
            return {"success": False, "error": str(e)}

    async def leave_channel(self, guild_id: int) -> dict:
        """Leave voice channel"""
        try:
            if guild_id in self.voice_clients:
                await self.voice_clients[guild_id].disconnect()
                del self.voice_clients[guild_id]

                # Clean up status
                self.is_playing[guild_id] = False
                self.is_paused[guild_id] = False
                if guild_id in self.current_track:
                    del self.current_track[guild_id]

                return {"success": True, "message": "Left voice channel"}
            else:
                return {"success": False, "error": "Bot not in voice channel"}

        except Exception as e:
            logger.error(f"Failed to leave channel: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self, guild_id: int) -> dict:
        """Get current playback status"""
        playing = self.is_playing.get(guild_id, False)
        current = self.current_track.get(guild_id, {})

        return {
            "playing": playing,
            "track": current.get("title", ""),
            "duration": current.get("duration", 0),
            "position": 0,
            "queue_length": 0
        }

# Initialize Discord Bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
music_bot = MusicBot()

# Discord Bot Events
@bot.event
async def on_ready():
    global bot_loop
    bot_loop = asyncio.get_event_loop()  # Store bot's event loop
    logger.info(f'{bot.user} has connected to Discord!')

# Add simple Discord commands (like working code)
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!play"):
        try:
            # Join voice channel
            if message.author.voice:
                channel_id = message.author.voice.channel.id
                guild_id = message.guild.id

                await music_bot.join_voice_channel(channel_id, guild_id)

                # Get URL from message
                url = message.content.split()[1] if len(message.content.split()) > 1 else ""
                if url:
                    result = await music_bot.play_music(guild_id, url)
                    if result["success"]:
                        await message.channel.send(f"🎵 {result['message']}")
                    else:
                        await message.channel.send(f"❌ {result['error']}")
                else:
                    await message.channel.send("❌ Please provide a URL")
            else:
                await message.channel.send("❌ You need to be in a voice channel")
        except Exception as e:
            logger.error(f"Discord command error: {e}")
            await message.channel.send(f"❌ Error: {e}")

# FastAPI Server (simplified)
app = FastAPI(title="Discord Music Bot API", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/play", response_model=MusicResponse)
async def api_play(request: MusicRequest):
    try:
        logger.info(f"Received play request: guild={request.guild_id}, channel={request.channel_id}, url={request.url}")

        guild_id = int(request.guild_id)
        channel_id = int(request.channel_id)
        url = request.url

        # Join channel first
        join_result = await music_bot.join_voice_channel(channel_id, guild_id)
        if not join_result:
            raise HTTPException(status_code=400, detail="Failed to join voice channel")

        # Play music
        result = await music_bot.play_music(guild_id, url)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return MusicResponse(
            success=result["success"],
            message=result["message"],
            title=result.get("title", ""),
            track_id=result.get("track_id", "")
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid guild_id or channel_id")
    except Exception as e:
        logger.error(f"API play error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop", response_model=MusicResponse)
async def api_stop(request: StopRequest):
    try:
        guild_id = int(request.guild_id)
        result = await music_bot.stop_music(guild_id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return MusicResponse(success=result["success"], message=result["message"])
    except Exception as e:
        logger.error(f"API stop error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{guild_id}", response_model=StatusResponse)
async def api_status(guild_id: str):
    try:
        guild_id_int = int(guild_id)
        result = music_bot.get_status(guild_id_int)
        return StatusResponse(**result)
    except Exception as e:
        logger.error(f"API status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_fastapi():
    """Run FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")

def run_bot():
    """Run Discord bot"""
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    # Start FastAPI server in background thread
    api_thread = threading.Thread(target=run_fastapi, daemon=True)
    api_thread.start()

    # Start Discord bot
    run_bot()
