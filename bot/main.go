package main

import (
	"context"
	"fmt"
	"log"
	application "mybot/content/application/Tatarbot"
	"mybot/content/handlers"
	manybath_service "mybot/content/services/Manybaht"
	music_services "mybot/content/services/Music"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/bwmarrin/discordgo"
	"github.com/joho/godotenv"
)

const (
	ShutdownTimeout   = 10 * time.Second
	ConnectionTimeout = 30 * time.Second
)

func main() {
	log.SetFlags(log.LstdFlags | log.Lshortfile)

	if err := godotenv.Load(); err != nil && !os.IsNotExist(err) {
		log.Fatalf("Failed to load environment: %v", err)
	}

	token := os.Getenv("DISCORD_TOKEN")
	if token == "" {
		log.Fatal("DISCORD_TOKEN is required")
	}
	// Create infrastructure (Discord session)
	session, err := discordgo.New("Bot " + token)
	if err != nil {
		log.Fatalf("Discord session creation failed: %v", err)
	}
	defer session.Close()

	// Setup Services
	manySvc := manybath_service.NewManybahtService()
	musicSvc := music_services.NewMusicService(session, "http://localhost:8080")
	botService := application.NewTatarBotService(manySvc, musicSvc)

	// Configure intents and handlers
	session.Identify.Intents = discordgo.IntentsGuildMessages |
		discordgo.IntentsMessageContent |
		discordgo.IntentsGuildVoiceStates |
		discordgo.IntentsGuilds

	// content.SetupMessageHandler(session)
	session.AddHandler(onReady)
	handlers.SetupMessageHandlers(session, botService)
	session.AddHandler(onDisconnect)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start bot
	if err := startBot(ctx, session); err != nil {
		log.Fatalf("Bot startup failed: %v", err)
	}

	waitForShutdown(cancel)
	gracefulShutdown(session)
}

func startBot(ctx context.Context, s *discordgo.Session) error {
	connectCh := make(chan error, 1)
	go func() { connectCh <- s.Open() }()

	select {
	case err := <-connectCh:
		if err != nil {
			return fmt.Errorf("Discord connection failed: %w", err)
		}
	case <-time.After(ConnectionTimeout):
		return fmt.Errorf("connection timeout")
	case <-ctx.Done():
		return fmt.Errorf("startup cancelled")
	}

	log.Printf("Bot online: %s#%s (ID: %s)", s.State.User.Username, s.State.User.Discriminator, s.State.User.ID)
	return nil
}

func waitForShutdown(cancel context.CancelFunc) {
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh
	cancel()
}

func gracefulShutdown(session *discordgo.Session) {
	ctx, cancel := context.WithTimeout(context.Background(), ShutdownTimeout)
	defer cancel()

	done := make(chan struct{})
	go func() {
		defer close(done)
		session.Close() // Discord session
		// TODO: Close another resource
	}()

	select {
	case <-done:
		log.Println("Shutdown completed")
	case <-ctx.Done():
		log.Println("Shutdown timed out")
	}
}

func onReady(s *discordgo.Session, r *discordgo.Ready) {
	log.Printf("Bot ready in %d guilds", len(r.Guilds))
	_ = s.UpdateGameStatus(0, "Responding to mentions")
}

func onDisconnect(s *discordgo.Session, _ *discordgo.Disconnect) {
	log.Println("Bot disconnected")
}
