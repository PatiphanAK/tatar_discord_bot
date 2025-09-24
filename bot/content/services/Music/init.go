package music_services

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"mybot/content/domain"
	"net/http"
	"strings"
	"time"

	"github.com/bwmarrin/discordgo"
)

// MusicRequest represents the payload sent to music bot API
type MusicRequest struct {
	GuildID   string `json:"guild_id"`
	ChannelID string `json:"channel_id"`
	URL       string `json:"url"`
	UserID    string `json:"user_id"`
}

// MusicResponse represents the response from music bot API
type MusicResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	TrackID string `json:"track_id,omitempty"`
	Title   string `json:"title,omitempty"`
	Error   string `json:"error,omitempty"`
}

// StatusResponse represents the current playback status
type StatusResponse struct {
	Playing     bool   `json:"playing"`
	Track       string `json:"track,omitempty"`
	Duration    int    `json:"duration,omitempty"`
	Position    int    `json:"position,omitempty"`
	QueueLength int    `json:"queue_length,omitempty"`
}

// MusicService handles communication with the Python music bot
type MusicService struct {
	session    *discordgo.Session
	apiBaseURL string
	httpClient *http.Client
}

// NewMusicService creates a new music service HTTP client
func NewMusicService(session *discordgo.Session, apiBaseURL string) *MusicService {
	if apiBaseURL == "" {
		apiBaseURL = "http://localhost:8080" // Default music bot API
	}

	// Ensure URL has proper scheme
	if !strings.HasPrefix(apiBaseURL, "http://") && !strings.HasPrefix(apiBaseURL, "https://") {
		apiBaseURL = "http://" + apiBaseURL
	}

	return &MusicService{
		session:    session,
		apiBaseURL: apiBaseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// findUserVoiceChannel finds which voice channel the user is in
func (m *MusicService) findUserVoiceChannel(guildID, userID string) (string, error) {
	guild, err := m.session.State.Guild(guildID)
	if err != nil {
		return "", fmt.Errorf("failed to get guild: %w", err)
	}

	for _, vs := range guild.VoiceStates {
		if vs.UserID == userID {
			return vs.ChannelID, nil
		}
	}

	return "", fmt.Errorf("user is not in a voice channel")
}

// makeAPIRequest makes HTTP request to music bot API
func (m *MusicService) makeAPIRequest(method, endpoint string, payload interface{}) (*MusicResponse, error) {
	var body bytes.Buffer
	if payload != nil {
		if err := json.NewEncoder(&body).Encode(payload); err != nil {
			return nil, fmt.Errorf("failed to encode payload: %w", err)
		}
	}

	url := m.apiBaseURL + endpoint
	req, err := http.NewRequestWithContext(context.Background(), method, url, &body)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := m.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	var result MusicResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("API error: %s", result.Error)
	}

	return &result, nil
}

// PlayMusic plays music from URL
func (m *MusicService) PlayMusic(cmd domain.BotCommand) (string, error) {
	if len(cmd.Args) == 0 {
		return "", fmt.Errorf("no URL provided")
	}

	url := cmd.Args[0]

	// Find user's voice channel
	channelID, err := m.findUserVoiceChannel(cmd.GuildID, cmd.UserID)
	if err != nil {
		return "", fmt.Errorf("failed to find voice channel: %w", err)
	}

	// Send request to music bot API
	request := MusicRequest{
		GuildID:   cmd.GuildID,
		ChannelID: channelID,
		URL:       url,
		UserID:    cmd.UserID,
	}

	response, err := m.makeAPIRequest("POST", "/play", request)
	if err != nil {
		return "", fmt.Errorf("failed to play music: %w", err)
	}

	if !response.Success {
		return "", fmt.Errorf("music bot error: %s", response.Error)
	}

	title := response.Title
	if title == "" {
		title = "Unknown Track"
	}

	return fmt.Sprintf("🎵 Now playing: **%s**", title), nil
}

// StopMusic stops current playback
func (m *MusicService) StopMusic(guildID string) (string, error) {
	request := map[string]string{"guild_id": guildID}

	response, err := m.makeAPIRequest("POST", "/stop", request)
	if err != nil {
		return "", fmt.Errorf("failed to stop music: %w", err)
	}

	if !response.Success {
		return "", fmt.Errorf("music bot error: %s", response.Error)
	}

	return "⏹️ Stopped playback", nil
}

// PauseMusic pauses current playback
func (m *MusicService) PauseMusic(guildID string) (string, error) {
	request := map[string]string{"guild_id": guildID}

	response, err := m.makeAPIRequest("POST", "/pause", request)
	if err != nil {
		return "", fmt.Errorf("failed to pause music: %w", err)
	}

	if !response.Success {
		return "", fmt.Errorf("music bot error: %s", response.Error)
	}

	return "⏸️ Paused playback", nil
}

// ResumeMusic resumes paused playback
func (m *MusicService) ResumeMusic(guildID string) (string, error) {
	request := map[string]string{"guild_id": guildID}

	response, err := m.makeAPIRequest("POST", "/resume", request)
	if err != nil {
		return "", fmt.Errorf("failed to resume music: %w", err)
	}

	if !response.Success {
		return "", fmt.Errorf("music bot error: %s", response.Error)
	}

	return "▶️ Resumed playback", nil
}

// GetStatus gets current playback status
func (m *MusicService) GetStatus(guildID string) (*StatusResponse, error) {
	url := fmt.Sprintf("%s/status/%s", m.apiBaseURL, guildID)
	req, err := http.NewRequestWithContext(context.Background(), "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := m.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	var status StatusResponse
	if err := json.NewDecoder(resp.Body).Decode(&status); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &status, nil
}

// LeaveVoiceChannel makes the music bot leave voice channel
func (m *MusicService) LeaveVoiceChannel(guildID string) (string, error) {
	request := map[string]string{"guild_id": guildID}

	response, err := m.makeAPIRequest("POST", "/leave", request)
	if err != nil {
		return "", fmt.Errorf("failed to leave channel: %w", err)
	}

	if !response.Success {
		return "", fmt.Errorf("music bot error: %s", response.Error)
	}

	return "👋 Left voice channel", nil
}

// IsPlaying checks if music is currently playing
func (m *MusicService) IsPlaying(guildID string) bool {
	status, err := m.GetStatus(guildID)
	if err != nil {
		return false
	}
	return status.Playing
}

// HealthCheck checks if music bot API is available
func (m *MusicService) HealthCheck() error {
	url := m.apiBaseURL + "/health"
	req, err := http.NewRequestWithContext(context.Background(), "GET", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := m.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("music bot API is not available: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("music bot API returned status: %d", resp.StatusCode)
	}

	return nil
}
