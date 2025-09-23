package application

import "mybot/content/domain"

type TatarBotService interface {
	HandleCommand(cmd domain.BotCommand) (string, error)
}
