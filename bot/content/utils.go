package content

import "github.com/bwmarrin/discordgo"

// getDisplayName returns the display name of a user
func getDisplayName(user *discordgo.User) string {
	if user.GlobalName != "" {
		return user.GlobalName
	}
	return user.Username
}
