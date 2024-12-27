# Track warned accounts per thread
warned_accounts = {}

def is_moderator(item, subreddit, log):
    """Check if user is a moderator of the subreddit"""
    try:
        author = item.author if hasattr(item, 'author') else None
        if not author:
            return False
            
        author_name = author.name.lower()
        thread_id = getattr(item, 'link_id', None) or getattr(item, 'id', 'unknown')
        
        # Initialize warned set for this thread if needed
        if thread_id not in warned_accounts:
            warned_accounts[thread_id] = set()
            
        # Special cases for automated/support accounts
        if author_name in ['automoderator', 'coinbasesupport', 'solana-modteam']:
            # Only log warning once per account per thread
            if author_name not in warned_accounts[thread_id]:
                log("⚠️  WARNING: %s is a system account - skipping", author.name)
                warned_accounts[thread_id].add(author_name)
            return True
            
        if not hasattr(subreddit, '_mod_cache'):
            subreddit._mod_cache = [mod.name.lower() for mod in subreddit.moderator()]
        
        is_mod = author_name in subreddit._mod_cache
        if is_mod and author_name not in warned_accounts[thread_id]:
            log("⚠️  WARNING: %s is a moderator - skipping", author.name)
            warned_accounts[thread_id].add(author_name)
        return is_mod
        
    except Exception as e:
        log("✗ Error checking moderator status: %s", str(e))
        return True

# Clean up old thread warnings periodically
def cleanup_warnings():
    """Remove warnings for old threads to prevent memory growth"""
    if len(warned_accounts) > 1000:  # Arbitrary limit
        warned_accounts.clear()

def is_likely_bot(username, log):
    """Check if username matches common bot patterns"""
    bot_patterns = ['bot', 'auto', '_bot', '-bot', 'Bot', 'robot', 'Robot']
    is_bot = any(pattern in username for pattern in bot_patterns)
    if is_bot:
        log("🤖 Detected likely bot username: %s", username)
    return is_bot

def is_valid_comment(comment, bot_username):
    """Check if a comment is valid for replying"""
    if not comment.author:
        return False
        
    if comment.author.name.lower() == bot_username.lower():
        return False
        
    if not comment.parent_id.startswith('t3_'):
        return False
        
    return True

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

def has_bot_activity(submission, bot_username, log):
    """Check if bot has already participated in thread"""
    # Modified to take bot_username as parameter
    try:
        all_comments = submission.comments.list()
        return any(
            comment.author and comment.author.name.lower() == bot_username.lower()
            for comment in all_comments
        )
    except Exception as e:
        log("Error checking thread history: %s", str(e))
        return True