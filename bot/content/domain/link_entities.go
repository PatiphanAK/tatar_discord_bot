package domain

import "math/big"

type EncryptionConfig struct {
	RSAExp *big.Int
	RSAMod *big.Int
}

type ConversionResult struct {
	Success      bool
	ConvertedURL string
	Platform     string
	Error        string
}

type LinkConverter interface {
	IsURL(input string) bool
	ConvertLink(url string) *ConversionResult
	DetectPlatform(url string) string
}
