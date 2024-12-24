import praw
from datetime import datetime
import time
from .config import REDDIT_CONFIG, KEYWORDS, SUBREDDITS

reddit = praw.Reddit(**REDDIT_CONFIG)

def should_respond(text):
    """Check if text contains relevant keywords"""
    text = text.lower()
    found_keywords = [keyword for keyword in KEYWORDS if keyword.lower() in text]
    if found_keywords:
        print("→ Keywords found:", ', '.join(found_keywords))
    return len(found_keywords) > 0

def has_bot_activity(submission):
    """Check if bot has already participated in thread"""
    try:
        bot_username = reddit.user.me().name
        submission.comments.replace_more(limit=None)
        all_comments = submission.comments.list()
        return any(
            comment.author and comment.author.name == bot_username 
            for comment in all_comments
        )
    except Exception as e:
        print(f"Error checking thread history: {e}")
        return True

def process_submission(submission):
    """Process a single submission"""
    # ... submission processing logic ...
