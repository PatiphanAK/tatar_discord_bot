package manybath_service

import (
	"encoding/base64"
	"fmt"
	"math/big"
	"mybot/content/domain"
	"net/url"
	"regexp"
	"strings"
)

type LinkConverterService struct {
	config *domain.EncryptionConfig
}

func NewLinkConverterService(config *domain.EncryptionConfig) *LinkConverterService {
	return &LinkConverterService{
		config: config,
	}
}

// Platform constants
const (
	PlatformYouTube     = "youtube"
	PlatformSpotify     = "spotify"
	PlatformAppleMusic  = "apple_music"
	PlatformUnsupported = "unsupported"
)

// Base URLs for different services
var baseURLs = map[string]string{
	"track":    "https://sp.laibaht.ovh/track/",
	"album":    "https://sp.laibaht.ovh/album/",
	"artist":   "https://sp.laibaht.ovh/artist/",
	"playlist": "https://sp.laibaht.ovh/playlist/",
	"wrapped":  "https://sp.laibaht.ovh/wrapped/",
}

// Regular expressions
var (
	spotifyRegex     = regexp.MustCompile(`https://open\.spotify\.com/(track|album|artist|playlist|wrapped)(?:/([a-zA-Z0-9-]+))?(?:/([a-zA-Z0-9-]+))?`)
	youtubeRegex     = regexp.MustCompile(`(?:https://www\.youtube\.com/(?:live|embed|shorts)/|youtu\.be/|\?v=)([a-zA-Z0-9_-]+)`)
	youtubeLiveRegex = regexp.MustCompile(`(?:https://www\.youtube\.com/(?:live|embed|shorts)/)([a-zA-Z0-9_-]+)`)
	appleRegex       = regexp.MustCompile(`https://music\.apple\.com/(?P<region>[a-z]{2})/(?P<type>song|album|playlist|artist)/(?P<name>[^/]+)/(?P<id>[a-zA-Z0-9.]+)`)
	urlRegex         = regexp.MustCompile(`^https?://[^\s]+$`)
)

// IsURL validates if input is a valid URL
func (s *LinkConverterService) IsURL(input string) bool {
	return urlRegex.MatchString(strings.TrimSpace(input))
}

// DetectPlatform identifies the platform from URL
func (s *LinkConverterService) DetectPlatform(url string) string {
	url = strings.ToLower(strings.TrimSpace(url))

	if strings.Contains(url, "youtube") || strings.Contains(url, "youtu.be") {
		return PlatformYouTube
	}
	if strings.Contains(url, "spotify.com") {
		return PlatformSpotify
	}
	if strings.Contains(url, "music.apple.com") {
		return PlatformAppleMusic
	}

	return PlatformUnsupported
}

// ConvertLink converts URL based on platform
func (s *LinkConverterService) ConvertLink(inputURL string) *domain.ConversionResult {
	if !s.IsURL(inputURL) {
		return &domain.ConversionResult{
			Success: false,
			Error:   "Invalid URL format",
		}
	}

	platform := s.DetectPlatform(inputURL)

	switch platform {
	case PlatformYouTube:
		return s.convertYouTubeURL(inputURL)
	case PlatformSpotify:
		return s.convertSpotifyURL(inputURL)
	case PlatformAppleMusic:
		return s.convertAppleMusicURL(inputURL)
	default:
		return &domain.ConversionResult{
			Success:  false,
			Platform: platform,
			Error:    "Unsupported platform",
		}
	}
}

// RSA encryption function
func (s *LinkConverterService) rsaEncrypt(text string) string {
	data := []byte(text)
	var result []byte

	// Calculate chunk size based on modulus bit length
	chunkSize := s.config.RSAMod.BitLen() / 8

	for i := 0; i < len(data); i += chunkSize {
		end := min(i+chunkSize, len(data))
		chunk := data[i:end]

		// Convert chunk to big.Int
		chunkInt := new(big.Int).SetBytes(chunk)

		// Perform RSA encryption: chunk^exp mod mod
		encrypted := new(big.Int).Exp(chunkInt, s.config.RSAExp, s.config.RSAMod)

		// Convert back to bytes with proper padding
		encryptedBytes := encrypted.Bytes()

		// Pad with zeros if necessary
		padded := make([]byte, chunkSize)
		copy(padded[chunkSize-len(encryptedBytes):], encryptedBytes)

		result = append(result, padded...)
	}

	// Convert to base64 and make URL-safe
	encoded := base64.StdEncoding.EncodeToString(result)
	encoded = strings.ReplaceAll(encoded, "+", "-")
	encoded = strings.ReplaceAll(encoded, "/", "_")
	encoded = strings.TrimRight(encoded, "=")

	return encoded
}

// YouTube URL conversion
func (s *LinkConverterService) convertYouTubeURL(inputURL string) *domain.ConversionResult {
	cleanedURL := s.cleanYouTubeURL(inputURL)

	parsedURL, err := url.Parse(cleanedURL)
	if err != nil {
		return &domain.ConversionResult{
			Success:  false,
			Platform: PlatformYouTube,
			Error:    "Invalid YouTube URL format",
		}
	}

	// Remove si and t parameters
	query := parsedURL.Query()
	query.Del("si")
	query.Del("t")

	// Encrypt video ID if present
	if videoID := query.Get("v"); videoID != "" {
		encryptedID := s.rsaEncrypt(videoID)
		query.Set("v", encryptedID)
	}

	// Encrypt playlist ID if present
	if playlistID := query.Get("list"); playlistID != "" {
		encryptedID := s.rsaEncrypt(playlistID)
		query.Set("list", encryptedID)
	}

	parsedURL.RawQuery = query.Encode()

	return &domain.ConversionResult{
		Success:      true,
		ConvertedURL: parsedURL.String(),
		Platform:     PlatformYouTube,
	}
}

// Spotify URL conversion
func (s *LinkConverterService) convertSpotifyURL(inputURL string) *domain.ConversionResult {
	matches := spotifyRegex.FindStringSubmatch(inputURL)
	if len(matches) < 3 {
		return &domain.ConversionResult{
			Success:  false,
			Platform: PlatformSpotify,
			Error:    "Invalid Spotify URL format",
		}
	}

	urlType := matches[1] // track, album, artist, playlist, wrapped
	id1 := matches[2]     // main ID
	id2 := matches[3]     // secondary ID (for wrapped URLs)

	if urlType == "" || id1 == "" {
		return &domain.ConversionResult{
			Success:  false,
			Platform: PlatformSpotify,
			Error:    "Missing required Spotify URL components",
		}
	}

	baseURL, exists := baseURLs[urlType]
	if !exists {
		return &domain.ConversionResult{
			Success:  false,
			Platform: PlatformSpotify,
			Error:    fmt.Sprintf("Unsupported Spotify URL type: %s", urlType),
		}
	}

	var idToEncrypt string
	if id2 != "" {
		// For wrapped URLs, use the secondary ID but remove "share-" prefix
		idToEncrypt = strings.TrimPrefix(id2, "share-")
	} else {
		idToEncrypt = id1
	}

	encryptedID := s.rsaEncrypt(idToEncrypt)

	return &domain.ConversionResult{
		Success:      true,
		ConvertedURL: baseURL + encryptedID,
		Platform:     PlatformSpotify,
	}
}

// Apple Music URL conversion
func (s *LinkConverterService) convertAppleMusicURL(inputURL string) *domain.ConversionResult {
	processedURL := s.processAppleMusicURL(inputURL)

	matches := appleRegex.FindStringSubmatch(processedURL)
	if len(matches) < 5 {
		return &domain.ConversionResult{
			Success:  false,
			Platform: PlatformAppleMusic,
			Error:    "Invalid Apple Music URL format",
		}
	}

	region := matches[1]
	urlType := matches[2]
	// name := matches[3] // not used in encryption
	id := matches[4]

	encryptedID := s.rsaEncrypt(id)
	convertedURL := fmt.Sprintf("https://ap.laibaht.ovh/%s/%s/%s", region, urlType, encryptedID)

	return &domain.ConversionResult{
		Success:      true,
		ConvertedURL: convertedURL,
		Platform:     PlatformAppleMusic,
	}
}

// Helper methods
func (s *LinkConverterService) cleanYouTubeURL(inputURL string) string {
	// Convert live/embed/shorts URLs to standard format
	if youtubeLiveRegex.MatchString(inputURL) {
		matches := youtubeLiveRegex.FindStringSubmatch(inputURL)
		if len(matches) > 1 {
			inputURL = fmt.Sprintf("https://www.youtube.com/watch?v=%s", matches[1])
		}
	}

	// Replace domains
	replacements := map[string]string{
		"music.youtube.com/": "play.laibaht.ovh/",
		"www.youtube.com/":   "play.laibaht.ovh/",
		"m.youtube.com/":     "play.laibaht.ovh/",
		"youtube.com/":       "play.laibaht.ovh/",
		"youtu.be/":          "play.laibaht.ovh/watch?v=",
	}

	result := inputURL
	for old, new := range replacements {
		result = strings.Replace(result, old, new, 1)
	}

	// Fix query parameters
	result = strings.Replace(result, "?si=", "&si=", 1)
	result = strings.Replace(result, "?t=", "&t=", 1)

	// Handle playlist URLs
	if !strings.Contains(result, "playlist?list=") {
		result = strings.Replace(result, "?list=", "&list=", 1)
	}

	return result
}

func (s *LinkConverterService) processAppleMusicURL(inputURL string) string {
	// Handle song URLs with ?i= parameter
	if strings.Contains(inputURL, "?i=") {
		inputURL = strings.Replace(inputURL, "/album/", "/song/", 1)
		re := regexp.MustCompile(`\?i=(\d+)`)
		matches := re.FindStringSubmatch(inputURL)
		if len(matches) > 1 {
			inputURL = re.ReplaceAllString(inputURL, "")
			// Replace the album ID with the song ID
			re2 := regexp.MustCompile(`/\d+$`)
			inputURL = re2.ReplaceAllString(inputURL, "/"+matches[1])
		}
	}

	return inputURL
}
