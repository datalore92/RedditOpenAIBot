import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Reddit Configuration
REDDIT_CONFIG = {
    'client_id': os.getenv('REDDIT_CLIENT_ID'),
    'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
    'user_agent': os.getenv('REDDIT_USER_AGENT'),
    'username': os.getenv('REDDIT_USERNAME'),
    'password': os.getenv('REDDIT_PASSWORD')
}

# OpenAI Configuration
OPENAI_CONFIG = {
    'api_key': os.getenv('OPENAI_API_KEY'),
    'model': 'gpt-4o-mini',
    'max_tokens': 40,
    'temperature': 0.7
}

# Monitoring Configuration
SUBREDDITS = [
    'CryptoMoonShots',
    'altcoin',
    'CryptoMarkets',
    'NFTsMarketplace',
    'NFT',
    'solana',
    'SolanaNFT'
]

KEYWORDS = [
    'altcoin',
    'shitcoin',
    'nft',
    'new coin',
    'moonshot',
    'solana',
    'sol'
]
