package music_services

import "mybot/content/domain"

type MusicServiceInterface interface {
	// Core playback functions
	PlayMusic(cmd domain.BotCommand) (string, error)
	StopMusic(guildID string) (string, error)
	PauseMusic(guildID string) (string, error)
	ResumeMusic(guildID string) (string, error)

	// Voice channel management
	LeaveVoiceChannel(guildID string) (string, error)

	// Status and information
	IsPlaying(guildID string) bool
	GetStatus(guildID string) (*StatusResponse, error)

	// Health and monitoring
	HealthCheck() error
}
