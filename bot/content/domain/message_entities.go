package domain

type MessageContext struct {
	Content        string
	IsPrivate      bool
	ConversationID string
	GuildID        string
	ChannelID      string
	AuthorID       string
}
