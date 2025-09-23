package application

import services "mybot/content/services/Manybaht"

type tatarBotService struct {
	// botRepo  domain.RepositoryInterface
	manybath *services.ManybahtService
	// authService domain.AuthenticationService // TODO: implement User role
}

func NewTatarBotService(
	// repo domain.RepositoryInterface,
	manybath *services.ManybahtService) *tatarBotService {
	return &tatarBotService{
		// botRepo:  repo,
		manybath: manybath,
	}
}
