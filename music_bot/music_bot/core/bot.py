import discord
from discord.ext import commands
import asyncio
from typing import Optional
from ..config.setting import Settings
from ..services.youtube import YouTubeService
from ..services.voice_manager import VoiceManager
from ..core.music_player import MusicPlayer
from ..models.music import Track
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class MusicBot(commands.Bot):
    """Discord Music Bot"""

    def __init__(self, settings: Settings):
        # Setup bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True

        super().__init__(
            command_prefix=settings.discord.command_prefix,
            intents=intents
        )

        self.settings = settings

        # Initialize services
        self.youtube_service = YouTubeService(settings.ytdl.to_dict())
        self.voice_manager = VoiceManager(self)
        self.music_player = MusicPlayer(
            self.voice_manager,
            self.youtube_service,
            settings.ffmpeg.to_dict()
        )

        # Setup event handlers
        self._setup_events()

    def _setup_events(self):
        """Setup bot event handlers"""

        @self.event
        async def on_ready():
            logger.info(f'{self.user} connected to Discord!')
            logger.info(f'Bot is in {len(self.guilds)} guilds')

        @self.event
        async def on_voice_state_update(member, before, after):
            """Handle voice state updates"""
            if member == self.user:
                return

            # Auto-leave if bot is alone
            if (before.channel and
                self.user in before.channel.members and
                len([m for m in before.channel.members if not m.bot]) == 0):

                guild_id = before.channel.guild.id
                logger.info(f"Bot alone, leaving guild {guild_id}")
                await asyncio.sleep(5)
                await self.voice_manager.leave_channel(guild_id)

        @self.event
        async def on_message(message):
            if message.author == self.user:
                return

            # Process commands
            await self.process_commands(message)

    async def play_music(self, guild_id: int, channel_id: int, url: str,
                        user_id: Optional[str] = None) -> Track:
        """Play music (API method)"""
        # Join channel
        await self.voice_manager.join_channel(channel_id, guild_id)

        # Play music
        return await self.music_player.play(guild_id, url, user_id)

    async def stop_music(self, guild_id: int) -> bool:
        """Stop music (API method)"""
        return self.music_player.stop(guild_id)

    async def pause_music(self, guild_id: int) -> bool:
        """Pause music (API method)"""
        return self.music_player.pause(guild_id)

    async def resume_music(self, guild_id: int) -> bool:
        """Resume music (API method)"""
        return self.music_player.resume(guild_id)

    async def leave_channel(self, guild_id: int) -> bool:
        """Leave voice channel (API method)"""
        return await self.voice_manager.leave_channel(guild_id)

    def get_status(self, guild_id: int) -> dict:
        """Get bot status (API method)"""
        playback_state = self.music_player.get_playback_state(guild_id)
        connected = self.voice_manager.is_connected(guild_id)

        voice_connection = None
        if connected:
            voice_client = self.voice_manager.get_voice_client(guild_id)
            if voice_client and voice_client.channel:
                voice_connection = {
                    "guild_id": guild_id,
                    "channel_id": voice_client.channel.id,
                    "channel_name": voice_client.channel.name,
                    "connected": True
                }

        return {
            "connected": connected,
            "playback_state": playback_state.dict(),
            "voice_connection": voice_connection
        }
