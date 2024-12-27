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

        # Initial reaction to the post
        response = generate_response(
            submission.title + "\n" + submission.selftext,
            context="Imagine you are the first person to reply to this post. Give your initial reaction."
        )
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
    from .thread_handler import thread_tracker_lock  # Add this import
    
    try:
        if has_bot_replied_to(comment, reddit_instance.user.me().name, log):
            return

        log("→ Processing reply to u/%s...", comment.author.name)
        
        # Build full context including conversation flow
        original_post = comment.submission
        context = f"""CONTEXT: This is a conversation:
1. Someone posted: "{original_post.title}"
   Their post said: "{original_post.selftext}"
2. Then u/{comment.author.name} replied saying: "{comment.body}"
3. You are now replying to u/{comment.author.name}'s comment.

You are casually joining this conversation. Reply to what u/{comment.author.name} said, not to the original post."""
        
        # Engaging in the discussion
        response = generate_response(context)
        if response:
            log("\n%s", '='*50)  # Add separator before success message
            reply = comment.reply(response)
            with thread_tracker_lock:  # Add lock protection
                state.responded_to_comments.add(comment.id)
            log("✓ Successfully replied to comment by u/%s", comment.author.name)
            log("→ Comment link: https://reddit.com%s", reply.permalink)
            
    except Exception as e:
        log("✗ Error in reply_to_comment: %s", str(e))
