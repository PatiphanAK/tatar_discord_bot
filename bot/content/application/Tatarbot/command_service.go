package application

import (
	"mybot/content/domain"
)

func (s *tatarBotService) HandleCommand(cmd domain.BotCommand) (string, error) {
	switch cmd.Name {
	case "manybaht":
		encoded := s.manybath.HandleCommand(cmd.Args)
		return encoded, nil

	case "play-gobot":
		reply, err := s.music.PlayMusic(cmd)
		if err != nil {
			return "", err
		}
		return reply, nil
	default:
		return "Unknown command", nil
	}
}

// func (s *TatarBotService) HandleMessage(msg domain.MessageContext) (string, error) {
// 	reply, err := s.botRepo.QueryLLM(msg.Content)
// 	if err != nil {
// 		return "", err
// 	}
// 	return reply, nil
// }
