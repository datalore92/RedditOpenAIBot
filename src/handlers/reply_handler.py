import time
import threading
from ..openai_handler import generate_response

def has_bot_replied_to(item, bot_name, log):
    """Check if bot has already replied to a specific post/comment"""
    try:
        if hasattr(item, 'refresh'):
            item.refresh()
        
        replies = item.comments.list() if hasattr(item, 'comments') else item.replies.list()
        
        has_replied = any(
            reply.author and reply.author.name.lower() == bot_name.lower()
            for reply in replies
        )
        
        if has_replied and log:
            log("⚠️  Bot has already replied to this item - skipping")
        
        return has_replied
    except Exception as e:
        if log:
            log("✗ Error checking reply history: %s", str(e))
        return True

def reply_to_op(submission, state, scheduled_time, log, reddit_instance):
    """Handle replying to the OP"""
    from .thread_handler import thread_tracker_lock  # Import here to avoid circular dependency
    
    try:
        if has_bot_replied_to(submission, reddit_instance.user.me().name, log):
            with thread_tracker_lock:
                state.replied_to_op = True
            return

        response = generate_response(submission.title + "\n" + submission.selftext)
        if response:
            log("\n%s", '='*50)  # Add separator before success message
            comment = submission.reply(response)
            log("✓ Successfully replied to OP")
            log("→ Comment link: https://reddit.com%s", comment.permalink)
            with thread_tracker_lock:
                state.replied_to_op = True
                
    except Exception as e:
        log("✗ Error replying to OP: %s", str(e))

def reply_to_comment(comment, state, current_time, log, reddit_instance):
    """Handle replying to a comment"""
    try:
        if has_bot_replied_to(comment, reddit_instance.user.me().name, log):
            return

        log("→ Processing reply to u/%s...", comment.author.name)
        
        # Build full context including original post and comment
        original_post = comment.submission
        context = f"""Original Post Title: {original_post.title}
Original Post Content: {original_post.selftext}

Comment by u/{comment.author.name}: {comment.body}"""
        
        # Generate response with full context
        response = generate_response(context)
        if response:
            log("\n%s", '='*50)  # Add separator before success message
            reply = comment.reply(response)
            log("✓ Successfully replied to comment by u/%s", comment.author.name)
            log("→ Comment link: https://reddit.com%s", reply.permalink)
            
    except Exception as e:
        log("✗ Error in reply_to_comment: %s", str(e))
