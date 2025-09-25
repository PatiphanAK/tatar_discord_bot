import discord
import asyncio
from typing import Dict, Optional
from ..models.music import VoiceConnection
from ..utils.exceptions import VoiceConnectionError
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class VoiceManager:
    """Voice connection management service"""

    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.connections: Dict[int, discord.VoiceClient] = {}

    async def join_channel(self, channel_id: int, guild_id: int) -> VoiceConnection:
        """Join a voice channel"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                raise VoiceConnectionError(f"Channel {channel_id} not found")

            if not isinstance(channel, discord.VoiceChannel):
                raise VoiceConnectionError("Channel is not a voice channel")

            # Disconnect from previous channel if connected
            await self._disconnect_if_connected(guild_id)

            # Connect to new channel
            voice_client = await channel.connect()
            self.connections[guild_id] = voice_client

            logger.info(f"Connected to {channel.name} in guild {guild_id}")

            return VoiceConnection(
                guild_id=guild_id,
                channel_id=channel_id,
                channel_name=channel.name,
                connected=True
            )

        except discord.ClientException as e:
            raise VoiceConnectionError(f"Discord connection error: {str(e)}")
        except Exception as e:
            raise VoiceConnectionError(f"Failed to join channel: {str(e)}")

    async def leave_channel(self, guild_id: int) -> bool:
        """Leave voice channel"""
        try:
            if guild_id in self.connections:
                voice_client = self.connections[guild_id]
                if voice_client.is_connected():
                    await voice_client.disconnect()
                del self.connections[guild_id]
                logger.info(f"Left voice channel in guild {guild_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error leaving channel: {e}")
            return False

    def get_voice_client(self, guild_id: int) -> Optional[discord.VoiceClient]:
        """Get voice client for guild"""
        return self.connections.get(guild_id)

    def is_connected(self, guild_id: int) -> bool:
        """Check if connected to voice channel"""
        voice_client = self.connections.get(guild_id)
        return voice_client is not None and voice_client.is_connected()

    async def _disconnect_if_connected(self, guild_id: int):
        """Disconnect from current channel if connected"""
        if guild_id in self.connections:
            voice_client = self.connections[guild_id]
            if voice_client.is_connected():
                await voice_client.disconnect()
            del self.connections[guild_id]

    def cleanup_disconnected(self) -> int:
        """Clean up disconnected voice clients"""
        disconnected = []
        for guild_id, voice_client in self.connections.items():
            if not voice_client.is_connected():
                disconnected.append(guild_id)

        for guild_id in disconnected:
            del self.connections[guild_id]
            logger.info(f"Cleaned up disconnected client for guild {guild_id}")

        return len(disconnected)
