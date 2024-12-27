import time
from datetime import datetime
from ..config import REPLY_WAIT_TIME, KEYWORDS
from .validation import is_valid_comment, is_moderator
from .thread_state import thread_tracker, thread_tracker_lock
from .reply_handler import reply_to_comment
from .auth_handler import reddit  # Add missing import

def process_comment(comment, state, reddit_instance, log):
    """Process a single comment"""
    if (is_valid_comment(comment, reddit_instance.user.me().name) and 
        not is_moderator(comment, comment.submission.subreddit, log)):
        
        # Only log once when we first see the comment
        if not hasattr(comment, 'reply_time'):
            comment.reply_time = time.time() + REPLY_WAIT_TIME
            log("\n%s", '='*50)
            log("→ Found new comment in thread: %s", comment.submission.title[:50])
            log("→ Comment by u/%s: %s", comment.author.name, comment.body[:100])
            log("→ Will reply in %d minutes", REPLY_WAIT_TIME//60)
        
        return comment
    return None
