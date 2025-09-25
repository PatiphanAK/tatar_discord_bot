import yt_dlp
import asyncio
from typing import Optional, Dict, Any
from ..models.music import Track
from ..utils.exceptions import YouTubeError
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class YouTubeService:
    """YouTube-DL service wrapper"""

    def __init__(self, ytdl_options: Dict[str, Any]):
        self.ytdl_options = ytdl_options
        self.ytdl = yt_dlp.YoutubeDL(ytdl_options)

    async def extract_track_info(self, url: str, requester_id: Optional[str] = None) -> Track:
        """Extract track information from URL"""
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None,
                lambda: self.ytdl.extract_info(url, download=False)
            )

            if not data:
                raise YouTubeError("No data found for URL")

            # Extract required information
            title = str(data.get('title', 'Unknown'))
            duration = int(data.get('duration', 0))
            uploader = str(data.get('uploader', 'Unknown'))
            playable_url = data.get('url')

            if not playable_url:
                raise YouTubeError("No playable URL found")

            track_id = str(hash(url + str(requester_id or '')))

            return Track(
                title=title,
                url=playable_url,
                duration=duration,
                uploader=uploader,
                track_id=track_id,
                requester_id=requester_id
            )

        except Exception as e:
            logger.error(f"Failed to extract track info: {e}")
            raise YouTubeError(f"Failed to process URL: {str(e)}")
