package services

import (
	"fmt"
	"math/big"
	"mybot/content/domain"
	"os"
	"strings"
)

// HandleCommand processes multiple arguments and returns formatted results
func (s *ManybahtService) HandleCommand(args []string) string {
	if len(args) == 0 {
		return "Please provide a URL to convert"
	}

	var results []string
	for _, arg := range args {
		if s.linkConverter.IsURL(arg) {
			result := s.processURL(arg)
			results = append(results, result)
		} else {
			results = append(results, fmt.Sprintf("❌ Invalid URL: %s", arg))
		}
	}
	return strings.Join(results, "\n")
}

// processURL handles URL conversion
func (s *ManybahtService) processURL(url string) string {
	result := s.linkConverter.ConvertLink(url)
	if result.Success {
		return fmt.Sprintf("✅ %s → %s", result.Platform, result.ConvertedURL)
	}
	return fmt.Sprintf("❌ Error: %s", result.Error)
}

// loadEncryptionConfig loads RSA configuration from environment variables
func loadEncryptionConfig() (*domain.EncryptionConfig, error) {
	expStr := "65537"
	modStr := "159020092212146830289645291"

	// Override with environment variables if set
	if envExp := os.Getenv("MANYBAHT_RSA_EXP"); envExp != "" {
		expStr = envExp
	}
	if envMod := os.Getenv("MANYBAHT_RSA_MOD"); envMod != "" {
		modStr = envMod
	}

	exp := new(big.Int)
	mod := new(big.Int)

	if _, ok := exp.SetString(expStr, 10); !ok {
		return nil, fmt.Errorf("invalid RSA exponent: %s", expStr)
	}
	if _, ok := mod.SetString(modStr, 10); !ok {
		return nil, fmt.Errorf("invalid RSA modulus: %s", modStr)
	}

	return &domain.EncryptionConfig{
		RSAExp: exp,
		RSAMod: mod,
	}, nil
}
