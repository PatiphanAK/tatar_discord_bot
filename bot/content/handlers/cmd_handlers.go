package handlers

import (
	application "mybot/content/application/Tatarbot"
	"mybot/content/domain"
	"strings"

	"github.com/bwmarrin/discordgo"
)

func SetupMessageHandlers(s *discordgo.Session, bot application.TatarBotService) {
	s.AddHandler(func(s *discordgo.Session, m *discordgo.MessageCreate) {
		if m.Author.ID == s.State.User.ID {
			return
		}

		if isCommand(m.Content) {

			cmd := parseCommand(m.Content)
			cmd.GuildID = m.GuildID
			cmd.ChannelID = m.ChannelID
			cmd.UserID = m.Author.ID
			reply, err := bot.HandleCommand(cmd)
			if err != nil {
				reply = err.Error()
			}
			if reply != "" {
				s.ChannelMessageSend(m.ChannelID, reply)
			}
		} else if isBotMentioned(s, m) {
			// Transform to MessageContext and call LLM
			// messageCtx := toMessageContext(m)

			// TODO: Implement LLM call
			// reply := bot.HandleLLMMessage(messageCtx)

			// if reply != "" {
			// 	s.ChannelMessageSend(m.ChannelID, reply)
			// }
		}
	})
}

func isCommand(content string) bool {
	return len(content) > 0 && (content[0] == '!' || content[0] == '/')
}

func parseCommand(content string) domain.BotCommand {
	parts := strings.Fields(content)
	if len(parts) == 0 {
		return domain.BotCommand{}
	}
	return domain.BotCommand{
		Name: parts[0][1:], // Remove prefix "!" , "/"
		Args: parts[1:],    // args
	}
}

// Check if this specific bot is mentioned anywhere in the message
func isBotMentioned(s *discordgo.Session, m *discordgo.MessageCreate) bool {
	// Check if our bot ID is in the message mentions
	for _, mention := range m.Mentions {
		if mention.ID == s.State.User.ID {
			return true
		}
	}
	return false
}

func toMessageContext(m *discordgo.MessageCreate) domain.MessageContext {
	return domain.MessageContext{
		Content:        m.Content,
		IsPrivate:      m.GuildID == "",
		ConversationID: m.GuildID,
		ChannelID:      m.ChannelID,
		AuthorID:       m.Author.ID,
	}
}
