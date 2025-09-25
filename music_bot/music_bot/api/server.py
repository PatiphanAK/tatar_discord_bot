from fastapi import FastAPI
import uvicorn
from music_bot.config.setting import Settings
from music_bot.core.bot import MusicBot
from music_bot.api.routes import create_music_routes

def create_app(music_bot: MusicBot) -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title="Discord Music Bot API",
        version="2.0.0",
        description="RESTful API for Discord Music Bot"
    )

    # Include routes
    router = create_music_routes(music_bot)
    app.include_router(router)

    return app

def run_server(app: FastAPI, settings: Settings):
    """Run FastAPI server"""
    uvicorn.run(
        app,
        host=settings.api.host,
        port=settings.api.port,
        log_level=settings.api.log_level,
        access_log=True
    )
