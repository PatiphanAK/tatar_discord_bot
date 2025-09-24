package application

import (
	manybath_service "mybot/content/services/Manybaht"
)

type tatarBotService struct {
	// botRepo  domain.RepositoryInterface
	manybath *manybath_service.ManybahtService
	// authService domain.AuthenticationService // TODO: implement User role
}

func NewTatarBotService(
	manybath *manybath_service.ManybahtService,
) *tatarBotService {
	return &tatarBotService{
		manybath: manybath,
	}
}
