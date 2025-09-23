package domain

type BotCommand struct {
	Name string
	Args []string
}
type ContentHandler struct {
	botMentionStr  string
	botMentionNick string
	botUserID      string
}
