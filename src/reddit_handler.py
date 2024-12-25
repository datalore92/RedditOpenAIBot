import praw
from datetime import datetime
import time
from .config import REDDIT_CONFIG, KEYWORDS, SUBREDDITS, REPLY_WAIT_TIME
from .utils import format_time_until, format_time_remaining
from .openai_handler import generate_response
import threading

reddit = praw.Reddit(**REDDIT_CONFIG)

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
    
    @property
    def is_complete(self):
        return self.replied_to_op and all(state['replied_to_comment'] for state in self.tracked_comments.values())

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
        

    # Handle comment replies
    if state and state.replied_to_op and not state.done:
        log("→ Looking for comments to reply to...")
        
        for comment in submission.comments.list():
            if not comment.author:
                log("→ Skipping deleted comment")
                continue
                
            # Hard-coded check for AutoModerator
            if comment.author.name.lower() == "automoderator":
                log("→ Skipping AutoModerator comment")
                continue
            
            # Check moderator status FIRST, before any other processing
            if is_moderator(comment, submission.subreddit, log):
                continue
            
            with thread_tracker_lock:
                # Initialize comment state if not tracked
                if comment.id not in state.tracked_comments:
                    state.tracked_comments[comment.id] = {
                        'reply_time': current_time + REPLY_WAIT_TIME,  # Set future timestamp for comment reply
                        'replied_to_comment': False
                    }
                    log("→ Will reply to comment %s in %d seconds", comment.id, REPLY_WAIT_TIME)
        
            comment_state = state.tracked_comments[comment.id]
            
            # Check if it's time to reply to the comment
            if not comment_state['replied_to_comment'] and current_time >= comment_state['reply_time']:
                # **Offload comment reply to a separate thread**
                comment_reply_thread = threading.Thread(target=reply_to_comment, args=(comment, comment_state, log))
                comment_reply_thread.start()
        
        # **Ensure threads remain tracked until all replies are done**
        with thread_tracker_lock:
            if state.is_complete:
                log("\n✓ Finished with thread: %s", state.submission.title[:50])
                thread_tracker.pop(submission.id, None)  # Remove now that replies are done

def reply_to_op(submission, state, current_time, log):
    """Handle replying to the OP"""
    try:
        delay = current_time - state.op_reply_time
        log("→ Processing reply %.1fs %s", delay, "overdue" if delay > 0 else "early")
        
        response = generate_response(submission.title + "\n" + submission.selftext)
        if response:
            comment = submission.reply(response)
            log("✓ Successfully replied to OP")
            log("→ Comment link: https://reddit.com%s", comment.permalink)
            with thread_tracker_lock:
                state.replied_to_op = True
        else:
            log("✗ Failed to generate response")
            
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
