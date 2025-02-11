# Reddit Bot

A Reddit bot that monitors cryptocurrency subreddits and responds to posts and comments using AI-generated responses. Runs in Docker with VPN protection.

## Features
- Console-based logging with real-time status updates
- Multi-threaded response handling
- Monitors multiple crypto subreddits simultaneously
- Smart rate limiting and response timing
- Moderator and bot detection
- Thread state tracking
- VPN integration for privacy
- Docker containerization

## New Features
- Improved comment tracking and response timing
- Full context awareness for AI responses (includes original post content)
- Smart duplicate comment detection
- Automatic thread cleanup after responses
- Better moderator and system account detection

## Prerequisites

- Docker and Docker Compose
- Windscribe VPN account
- Reddit API credentials
- OpenAI API key

## Setup

1. Copy `.env.example` to `.env` and fill in your credentials
2. Set up VPN:
   - Place your Windscribe OpenVPN configuration in `configs/windscribe.ovpn`
   - Create `configs/credentials` with your Windscribe credentials:
     ```
     username
     password
     ```
3. Build the Docker container:
   ```bash
   docker-compose build
   ```

## Running the Bot

1. For Windows PowerShell:
   ```powershell
   .\run.ps1
   ```

   For Linux/Mac:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

   Or run the commands manually:
   ```bash
   docker-compose up
   ```

3. The startup script will:
   - Configure DNS
   - Establish VPN connection
   - Verify IP change
   - Launch the bot

## Security Notes

- Never commit `.env` file or VPN configs
- Check `.gitignore` to ensure sensitive files are excluded
- Use example files for templates only
- VPN credentials are mounted as volumes
- Network traffic is routed through VPN
- Container runs with limited privileges

## Configuration

Create a `.env` file with the following variables:
```env
# Reddit API Credentials
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_user_agent
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password

# OpenAI API
OPENAI_API_KEY=your_openai_key

# VPN Settings (optional)
VPN_PROVIDER=windscribe
VPN_REGION=us
```

## Monitoring

- View logs in real-time: `docker-compose logs -f`
- Check VPN status: `docker exec reddit-bot-01 ip addr show tun0`
- Monitor bot status through the console output and logs
- Logs are stored in:
  - `logs/bot.log`: Bot activity
  - `logs/status.log`: OpenVPN status
  - `logs/vpn_status.log`: Detailed VPN connection info
    ```
    VPN Status Log - [timestamp]
    ----------------------------------------
    Original IP: x.x.x.x
    Original Location: City, Country
    Original ISP: Internet Provider
    ----------------------------------------
    VPN Connection Established - [timestamp]
    ----------------------------------------
    New IP: y.y.y.y
    VPN Location: City, State, Country
    VPN ISP: VPN Provider
    ----------------------------------------
    ```

## Configuration Files

- `config.py`: Subreddits, keywords, and timing settings
- `.env`: API credentials and secrets
- `openai_handler.py`: AI response configuration
- `startup.sh`: VPN and container initialization
- `docker-compose.yml`: Container configuration

## Container Infrastructure

- Base Image: Arch Linux (latest)
- Python environment: Python 3.11+
- System packages:
  - OpenVPN
  - Curl
  - Base-devel
  - Python dependencies

### Container Management

Common Docker commands:
```bash
# View all containers
docker ps -a

# View all images
docker images

# Enter container shell
docker exec -it reddit-bot-01 /bin/bash

# View container logs
docker logs reddit-bot-01

# Inspect container details
docker inspect reddit-bot-01

# Clean up unused images
docker image prune -a --filter "until=24h"  # Remove images older than 24h
docker image prune -a  # Remove all unused images
docker system prune -a  # Remove all unused containers, images, and volumes
```

### Build Cache Management

Docker maintains a build cache to speed up subsequent builds:
```powershell
# Normal build (uses cache)
.\run.ps1

# Clean build (no cache)
.\run.ps1 -clean

# View build cache
docker builder prune -a

# Clear build cache
docker builder prune -af
```

The build cache:
- Persists even after removing images
- Speeds up builds by reusing layers
- Is separate from the images themselves
- Located in Docker's data directory
- Can be viewed with `docker builder ls`

## Development

### Git Commands
```bash
# Check status of changes
git status

# Add changes
git add .

# Commit changes with message
git commit -m "Your descriptive message here"

# Push to GitHub
git push origin main
```

Remember to:
- Use clear commit messages
- Never commit sensitive files
- Update .gitignore as needed
- Generate new access token if expired

## Bot Behavior
- Waits 2 minutes before replying to new posts
- Monitors each post for comments
- Waits 2 minutes before replying to comments
- Stops monitoring a thread after:
  1. Replying to the original post
  2. Replying to one comment
- Avoids replying to:
  - Moderators
  - AutoModerator
  - CoinbaseSupport
  - Solana-ModTeam
  - Other bots
  - Its own comments

## Console Output
- Real-time thread discovery
- Comment detection and timing
- Success/failure notifications
- VPN status updates
- Error reporting
- Thread completion status
