from datetime import datetime
import time
import threading
from ..config import REPLY_WAIT_TIME
from ..utils.time_utils import format_time_until
from .reply_handler import reply_to_op, reply_to_comment
from .validation import is_valid_comment, is_moderator
from .thread_state import ThreadState, thread_tracker, thread_tracker_lock
from .comment_handler import process_comment

def track_new_thread(submission, log, reddit_instance):
    """Start tracking a new thread"""
    with thread_tracker_lock:
        if submission.id not in thread_tracker:
            state = ThreadState(submission)
            thread_tracker[submission.id] = state
            
            log("\n%s", '='*50)
            log("Found new post in r/%s", submission.subreddit.display_name)
            log("Title: %s", submission.title)
            log("URL: https://reddit.com%s", submission.permalink)
            log(f"→ Will reply to OP in {REPLY_WAIT_TIME//60} minutes 0 seconds")
            log("→ Also monitoring this thread for comments...")
            log("→ Still monitoring for other new threads...")
            
            # Schedule both the OP reply and comment monitoring
            op_timer = threading.Timer(
                REPLY_WAIT_TIME,
                reply_to_op,
                args=(submission, state, time.time() + REPLY_WAIT_TIME, log, reddit_instance)
            )
            op_timer.daemon = True
            op_timer.start()
            
            # Start a separate thread to monitor comments
            monitor_thread = threading.Thread(
                target=monitor_thread_comments,
                args=(submission, state, log, reddit_instance),
                daemon=True
            )
            monitor_thread.start()
            
            return state
    return None

def monitor_thread_comments(submission, state, log, reddit_instance):
    """Continuously monitor a thread for new comments"""
    pending_comments = {}  # Add this to track pending comments
    
    while not state.is_complete:
        try:
            fresh_submission = reddit_instance.submission(id=submission.id)
            fresh_submission.comments.replace_more(limit=0)
            
            if state.replied_to_op and len(state.responded_to_comments) > 0:
                log("\n[%s]", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                log("→ Stopping monitoring after replying to comment in: %s", submission.title[:50])
                state.waiting_for_op_responses = False
                remove_thread(submission.id, log)
                break
            
            for comment in fresh_submission.comments:
                if (comment.id not in state.responded_to_comments and 
                    comment.id not in pending_comments):  # Only process if not already pending
                    
                    processed = process_comment(comment, state, reddit_instance, log)
                    if processed:
                        pending_comments[comment.id] = processed
            
            # Check pending comments for reply timing
            current_time = time.time()
            for comment_id, pending_comment in list(pending_comments.items()):
                if current_time >= pending_comment.reply_time:
                    reply_thread = threading.Thread(
                        target=reply_to_comment,
                        args=(pending_comment, state, current_time, log, reddit_instance)
                    )
                    reply_thread.start()
                    state.responded_to_comments.add(comment_id)
                    pending_comments.pop(comment_id)

            time.sleep(10)
        except Exception as e:
            log("✗ Error monitoring thread comments: %s", str(e))
            time.sleep(30)

def remove_thread(submission_id, log):
    """Remove a thread from tracking"""
    with thread_tracker_lock:
        if submission_id in thread_tracker:
            thread = thread_tracker.pop(submission_id)
            log("\n[%s]", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            log("✓ Stopped tracking thread: %s", thread.submission.title[:50])
            log("→ Replied to OP and %d comments", len(thread.responded_to_comments))