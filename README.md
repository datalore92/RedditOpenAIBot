# Reddit Solana Bot

A Reddit bot that monitors cryptocurrency subreddits and responds to posts and comments using AI-generated responses.

## Features

- Interactive curses-based UI for real-time monitoring
- Multi-threaded response handling
- Monitors multiple crypto subreddits simultaneously
- Smart rate limiting and response timing
- Moderator detection and bot avoidance
- Comprehensive logging system
- Configurable keywords and subreddits

## Setup

1. Clone the repository
2. Run the setup script: `./setup.sh`
3. Copy `.env.example` to `.env` and fill in your credentials
4. Run the bot: `python -m src.bot`

## Configuration

Create a `.env` file with the following variables:
```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_user_agent
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key
```

## Usage

- The bot runs with a curses interface by default
- Press 'q' to quit the bot gracefully
- Logs are saved to `bot.log`
- Set `USE_CURSES = False` in `bot.py` for terminal-only mode

## Configuration Files

- `config.py`: Subreddits, keywords, and timing settings
- `.env`: API credentials and secrets
- `openai_handler.py`: AI response configuration
