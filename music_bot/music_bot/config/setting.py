import os
from dataclasses import dataclass
from typing import Dict, Union, Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class DiscordConfig:
    """Discord bot configuration"""
    token: str
    command_prefix: str = "!"

    def __post_init__(self):
        if not self.token:
            raise ValueError("DISCORD_TOKEN environment variable is required")

@dataclass
class YTDLConfig:
    """YouTube-DL configuration"""
    format: str = 'bestaudio/best'
    quiet: bool = True
    no_warnings: bool = True
    extractaudio: bool = True
    audioformat: str = 'opus'
    noplaylist: bool = True

    def to_dict(self) -> Dict[str, Union[str, bool]]:
        return {
            'format': self.format,
            'quiet': self.quiet,
            'no_warnings': self.no_warnings,
            'extractaudio': self.extractaudio,
            'audioformat': self.audioformat,
            'noplaylist': self.noplaylist,
        }

@dataclass
class FFMPEGConfig:
    """FFMPEG configuration"""
    before_options: str = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
    options: str = '-vn -filter:a "volume=0.25"'

    def to_dict(self) -> Dict[str, str]:
        return {
            'before_options': self.before_options,
            'options': self.options
        }

@dataclass
class APIConfig:
    """API server configuration"""
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "info"

@dataclass
class Settings:
    """Application settings"""
    discord: DiscordConfig
    ytdl: YTDLConfig
    ffmpeg: FFMPEGConfig
    api: APIConfig

    @classmethod
    def load(cls) -> 'Settings':
        """Load settings from environment"""
        return cls(
            discord=DiscordConfig(token=os.getenv('DISCORD_TOKEN', '')),
            ytdl=YTDLConfig(),
            ffmpeg=FFMPEGConfig(),
            api=APIConfig()
        )
