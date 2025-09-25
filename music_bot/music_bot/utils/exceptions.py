class MusicBotException(Exception):
    """Base exception for music bot"""
    pass

class VoiceConnectionError(MusicBotException):
    """Voice connection related errors"""
    pass

class PlaybackError(MusicBotException):
    """Playback related errors"""
    pass

class YouTubeError(MusicBotException):
    """YouTube-DL related errors"""
    pass
