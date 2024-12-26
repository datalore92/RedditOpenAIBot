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
    'model': 'gpt-4o-mini',  # Corrected model name from 'gpt-4o-mini' to 'gpt-4'
    'max_tokens': 50,
    'temperature': 0.7
}

# Monitoring Configuration
SUBREDDITS = [
    # Major Crypto Subreddits
    'CryptoMoonShots',
    'altcoin',
    'CryptoMarkets',
    #'CryptoCurrency',
    'CryptoTechnology',
    'CryptoTrading',
    'cryptostreetbets',
    'SatoshiStreetBets',
    'CryptoMarsShots',
    'AllCryptoBets',
    'CryptoGemDiscovery',
    
    # Solana Specific
    'solana',
    #'SolanaNFT',
    'solanadev',
    
    # NFT Related
    #'NFT',
    #'NFTsMarketplace',
    #'NFTExchange',
    #'opensea',
    
    # Trading Related
    'binanceUS',
    'CoinBase',
    'kucoin',
    'kraken',
    'ftx',
    
    # Meme Coins
    'SHIBArmy',
    'dogecoin',
    'memecoin',
    'memecoins',

    # Other
    #'dota2', 
    #'learndota2',
    #'securityguards',
    #'4chan',
    #'antisocial', 
    #'antiwork'
]

KEYWORDS = [
    #'altcoin',
    #'shitcoin',
    #'nft',
    #'new coin',
    #'moonshot',
    #'solana',
    #'sol'
]

# Timing Configuration
REPLY_WAIT_TIME = 121  # Time in seconds before replying to OP or comments
