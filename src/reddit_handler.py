import praw
from datetime import datetime
import time
import os
from .config import REDDIT_CONFIG, KEYWORDS, SUBREDDITS, REPLY_WAIT_TIME
from .utils import format_time_until, format_time_remaining
from .openai_handler import generate_response
import threading

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

# Force fresh authentication before creating client
force_fresh_auth()

# Initialize Reddit client with fresh auth
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
except Exception as e:
    print(f"Authentication failed: {e}")
    raise

# Track threads and their states
thread_tracker = {}

# Initialize a threading lock for thread_tracker
thread_tracker_lock = threading.Lock()

class ThreadState:
    def __init__(self, submission):
        self.submission = submission
        self.replied_to_op = False
        self.op_reply_time = time.time() + REPLY_WAIT_TIME  # Set future timestamp for OP reply
        self.tracked_comments = {}
        self.done = False
        self.last_not_met_log_time = 0  # Added to track last "not met" log time
        self.last_message_times = {}  # Track when messages were last logged
    
    @property
    def is_complete(self):
        return self.replied_to_op and all(state['replied_to_comment'] for state in self.tracked_comments.values())

    def should_log(self, message_type, throttle_seconds=10):
        """Check if we should log this message type based on throttling"""
        current_time = time.time()
        last_time = self.last_message_times.get(message_type, 0)
        
        if current_time - last_time >= throttle_seconds:
            self.last_message_times[message_type] = current_time
            return True
        return False

def is_moderator(comment, subreddit, log):
    """Check if user is a moderator of the subreddit"""
    try:
        if not comment.author:
            return False
        author_name = comment.author.name.lower()
        # Cache moderator list to avoid repeated API calls
        if not hasattr(subreddit, '_mod_cache'):
            subreddit._mod_cache = [mod.name.lower() for mod in subreddit.moderator()]
        
        is_mod = author_name in subreddit._mod_cache
        if is_mod:
            # Only log mod warnings once per mod per thread
            mod_warn_key = f"mod_warn_{author_name}"
            if not hasattr(subreddit, mod_warn_key):
                setattr(subreddit, mod_warn_key, True)
                log("⚠️  WARNING: %s is a moderator - skipping", comment.author.name)
        return is_mod
    except Exception as e:
        log("✗ Error checking moderator status: %s", str(e))
        return True  # Assume it's a mod if we can't check, to be safe

def is_likely_bot(username, log):
    """Check if username matches common bot patterns"""
    bot_patterns = ['bot', 'auto', '_bot', '-bot', 'Bot', 'robot', 'Robot']
    is_bot = any(pattern in username for pattern in bot_patterns)
    if is_bot:
        log("🤖 Detected likely bot username: %s", username)
    return is_bot

def check_tracked_threads(log):
    """Check all tracked threads for new comments and OP replies"""
    # Assert that log is not None
    assert log is not None, "Log function is None in check_tracked_threads."
    assert callable(log), "Log is not callable in check_tracked_threads."
    
    with thread_tracker_lock:
        if not thread_tracker:
            log("→ No threads being tracked")
            return
        
        log("→ Checking %d tracked threads for new comments...", len(thread_tracker))
    
    for submission_id, state in list(thread_tracker.items()):
        try:
            submission = reddit.submission(id=submission_id)
            submission.comments.replace_more(limit=0)  # Refresh comments
            process_submission(submission, state, log=log)  # Ensure correct arguments
        except Exception as e:
            log("✗ Error checking thread %s: %s", submission_id, str(e))
            continue

def process_submission(submission, state=None, force_reply=False, log=None):
    """Process a single submission and its comments"""
    # Assert that log is not None
    assert log is not None, "Log function is None in process_submission."
    assert callable(log), "Log is not callable in process_submission."
    
    current_time = time.time()
    
    with thread_tracker_lock:
        # Initialize state if needed
        if state is None:
            if submission.id in thread_tracker:
                state = thread_tracker[submission.id]
            elif should_respond(submission.title + submission.selftext, log):
                state = ThreadState(submission)
                thread_tracker[submission.id] = state
                log("\n%s", '='*50)
                log("Found new post in r/%s", submission.subreddit.display_name)
                log("Title: %s", submission.title)
                log("URL: https://reddit.com%s", submission.permalink)
                log("→ Will reply to OP in %s", format_time_until(state.op_reply_time))
                return
    
    if not state:
        return

    # **Added Debug Logs Below**
    
    # Handle OP reply with priority for overdue posts
    if not state.replied_to_op and (force_reply or current_time >= state.op_reply_time):
        log("→ Condition to reply met: force_reply=%s, current_time >= op_reply_time=%s", 
            force_reply, current_time >= state.op_reply_time)
        
        # **Offload reply operation to a separate thread**
        reply_thread = threading.Thread(target=reply_to_op, args=(submission, state, current_time, log))
        reply_thread.start()

        # Remove the thread from tracking after scheduling OP reply
        with thread_tracker_lock:
            if submission.id in thread_tracker:
                log("\n✓ Done with thread: %s", submission.title[:50])
                thread_tracker.pop(submission.id, None)
        return

    # Comment reply handling no longer needed:
    # ...commented out or removed code that processes comments...

def has_bot_replied_to(item, bot_name=None, log=None):
    """Check if bot has already replied to a specific post/comment"""
    if not bot_name:
        bot_name = reddit.user.me().name.lower()
    try:
        # Force-refresh the comments
        if hasattr(item, 'refresh'):
            item.refresh()
        
        # Get all replies
        if hasattr(item, 'comments'):  # For submissions
            replies = item.comments.list()
        else:  # For comments
            item.refresh()
            replies = item.replies.list()
        
        # Check if bot has replied
        has_replied = any(
            reply.author and reply.author.name.lower() == bot_name
            for reply in replies
        )
        
        if has_replied and log:
            log("⚠️  Bot has already replied to this item - skipping")
        
        return has_replied
    except Exception as e:
        if log:
            log("✗ Error checking reply history: %s", str(e))
        return True  # Assume replied on error to be safe

def reply_to_op(submission, state, current_time, log):
    """Handle replying to the OP with rate limit handling"""
    try:
        # Check for existing reply first
        if has_bot_replied_to(submission, log=log):
            with thread_tracker_lock:
                state.replied_to_op = True
            return

        delay = current_time - state.op_reply_time
        log("→ Processing reply %.1fs %s", delay, "overdue" if delay > 0 else "early")
        
        # Add rate limit handling
        max_retries = 3
        retry_delay = 60  # Wait 60 seconds between retries
        
        for attempt in range(max_retries):
            try:
                response = generate_response(submission.title + "\n" + submission.selftext)
                if response:
                    comment = submission.reply(response)
                    log("✓ Successfully replied to OP")
                    log("→ Comment link: https://reddit.com%s", comment.permalink)
                    with thread_tracker_lock:
                        state.replied_to_op = True
                    return
            except Exception as e:
                if "RATELIMIT" in str(e):
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        log(f"Rate limited. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                log("✗ Error replying to OP: %s", str(e))
                break
                
    except Exception as e:
        log("✗ Error replying to OP: %s", str(e))

def should_respond(text, log):
    """Check if text contains relevant keywords"""
    if not KEYWORDS:  # If no keywords defined, respond to everything
        log("→ No keywords set - replying to all posts")
        return True
        
    text = text.lower()
    found_keywords = [keyword for keyword in KEYWORDS if keyword.lower() in text]
    if found_keywords:
        log("→ Keywords found: %s", ', '.join(found_keywords))
        return True
    return False

def has_bot_activity(submission, log):
    """Check if bot has already participated in thread"""
    try:
        bot_username = reddit.user.me().name.lower()
        all_comments = submission.comments.list()
        return any(
            comment.author and comment.author.name.lower() == bot_username 
            for comment in all_comments
        )
    except Exception as e:
        log("Error checking thread history: %s", str(e))
        return True
