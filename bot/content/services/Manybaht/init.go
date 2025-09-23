package services

import (
	"log"
	"mybot/content/domain"
)

type ManybahtService struct {
	linkConverter domain.LinkConverter
}

func NewManybahtService() *ManybahtService {
	// Load RSA configuration from environment
	config, err := loadEncryptionConfig()
	if err != nil {
		log.Fatal("Failed to load encryption config:", err)
	}

	// Initialize services
	linkConverter := NewLinkConverterService(config)

	return &ManybahtService{
		linkConverter: linkConverter,
	}
}
