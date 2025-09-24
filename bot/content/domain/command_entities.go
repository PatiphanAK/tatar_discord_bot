package domain

type BotCommand struct {
	Name      string
	Args      []string
	GuildID   string
	ChannelID string
	UserID    string
}
type ContentHandler struct {
	botMentionStr  string
	botMentionNick string
	botUserID      string
}
