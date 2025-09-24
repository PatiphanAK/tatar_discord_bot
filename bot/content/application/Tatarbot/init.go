package application

import (
	manybath_service "mybot/content/services/Manybaht"
	music_services "mybot/content/services/Music"
)

type tatarBotService struct {
	// botRepo  domain.RepositoryInterface
	manybath *manybath_service.ManybahtService
	music    music_services.MusicServiceInterface
	// authService domain.AuthenticationService // TODO: implement User role
}

func NewTatarBotService(
	manybath *manybath_service.ManybahtService,
	music music_services.MusicServiceInterface,
) *tatarBotService {
	return &tatarBotService{
		manybath: manybath,
		music:    music,
	}
}
