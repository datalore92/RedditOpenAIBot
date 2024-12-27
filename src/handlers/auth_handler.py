import os
import praw
from ..config import REDDIT_CONFIG

def force_fresh_auth():
    """Force fresh authentication by clearing PRAW token files"""
    token_paths = [
        os.path.expanduser('~/.config/praw.ini'),
        os.path.expanduser('~/.cache/praw.ini'),
        os.path.expanduser('~/.local/share/praw.ini')
    ]
    for path in token_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

# Global reddit instance
reddit = None

def initialize_reddit():
    """Initialize and return authenticated Reddit client"""
    global reddit
    if reddit is not None:
        return reddit
        
    force_fresh_auth()
    
    reddit = praw.Reddit(
        client_id=REDDIT_CONFIG['client_id'],
        client_secret=REDDIT_CONFIG['client_secret'],
        user_agent=REDDIT_CONFIG['user_agent'],
        username=REDDIT_CONFIG['username'],
        password=REDDIT_CONFIG['password'],
        ratelimit_seconds=300,
        check_for_updates=False,
        check_for_async=False
    )
    
    # Verify authentication
    try:
        username = reddit.user.me().name
        print(f"Authenticated as: {username}")
        return reddit
    except Exception as e:
        print(f"Authentication failed: {e}")
        raise
