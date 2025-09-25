import asyncio
import threading
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from music_bot.config.setting import Settings
from music_bot.core.bot import MusicBot
from music_bot.api.server import create_app, run_server
from music_bot.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    """Main entry point"""
    try:
        # Load settings
        settings = Settings.load()
        logger.info("Settings loaded successfully")

        # Create music bot
        music_bot = MusicBot(settings)
        logger.info("Music bot created")

        # Store bot's loop reference for cross-thread access
        music_bot._bot_loop = None

        # Override the on_ready event to capture the loop
        original_on_ready = music_bot._setup_events
        def setup_events_with_loop():
            original_on_ready()

            @music_bot.event
            async def on_ready():
                # Store the bot's event loop
                music_bot._bot_loop = asyncio.get_event_loop()
                logger.info(f'{music_bot.user} connected to Discord!')
                logger.info(f'Bot is in {len(music_bot.guilds)} guilds')
                logger.info("Bot event loop stored for API access")

        music_bot._setup_events = setup_events_with_loop
        music_bot._setup_events()

        # Create FastAPI app
        app = create_app(music_bot)
        logger.info("FastAPI app created")

        # Start API server in background thread
        api_thread = threading.Thread(
            target=run_server,
            args=(app, settings),
            daemon=True,
            name="FastAPI-Thread"
        )
        api_thread.start()
        logger.info("FastAPI server started on background thread")

        # Start Discord bot (blocking)
        logger.info("Starting Discord bot...")
        music_bot.run(settings.discord.token, log_handler=None)

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

if __name__ == "__main__":
    main()
