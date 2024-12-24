# Reddit Solana Bot

A Reddit bot that monitors cryptocurrency subreddits and responds to posts and comments about Solana and other crypto topics.

## Setup

1. Clone the repository
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in your credentials
6. Run the bot: `python bot.py`

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

## Features

- Monitors multiple crypto subreddits
- Responds to posts and comments containing specific keywords
- Uses OpenAI to generate contextual responses
- Avoids duplicate responses
- Only responds to new posts
