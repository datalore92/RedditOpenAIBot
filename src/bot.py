import time
from datetime import datetime
import sys
import termios
import tty
import threading
from .config import SUBREDDITS, KEYWORDS, REPLY_WAIT_TIME
from .handlers.auth_handler import initialize_reddit
from .handlers.thread_handler import track_new_thread
from .ui.logger import BotLogger

# Log File Configuration
LOG_FILE = '/app/logs/bot.log'

def check_for_quit():
    """Check for 'q' keypress without blocking"""
    try:
        # Save terminal settings
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        
        if sys.stdin.read(1) == 'q':
            return True
        
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    except:
        pass
    return False

def monitor_keyboard():
    """Monitor for 'q' press"""
    while True:
        if check_for_quit():
            print("\nShutdown requested. Cleaning up...")
            sys.exit(0)
        time.sleep(0.1)

def monitor_reddit():
    """Monitor Reddit in standard logging mode"""
    logger = BotLogger(LOG_FILE)
    reddit = initialize_reddit()
    
    try:
        logger.log("✓ Monitoring subreddits: " + ", ".join(SUBREDDITS))
        logger.log(f"Bot authenticated as: u/{reddit.user.me().name}")
        logger.log("\n⚡ Starting bot operations...")
        logger.log(f"→ Will reply to new posts after {REPLY_WAIT_TIME//60} minutes")
        logger.log(f"→ Will reply to comments after {REPLY_WAIT_TIME//60} minutes")
        logger.log("→ Continuously monitoring all threads...\n")
        
        # Start keyboard monitoring in separate thread
        keyboard_thread = threading.Thread(target=monitor_keyboard, daemon=True)
        keyboard_thread.start()
        
        logger.log("Press 'q' to quit gracefully")
        
        subreddit = reddit.subreddit('+'.join(SUBREDDITS))
        while True:  # Use while loop instead of for loop
            try:
                for submission in subreddit.stream.submissions(skip_existing=True, pause_after=0):
                    if submission:
                        track_new_thread(submission, logger.log, reddit)
                    time.sleep(0.1)
            except Exception as e:
                logger.log("✗ Error in submission stream: %s", str(e))
                time.sleep(30)
                continue
            
    except (KeyboardInterrupt, SystemExit):
        logger.log("Bot shutdown requested. Shutting down gracefully...")
    finally:
        logger.log("Bot stopped successfully.")
        sys.exit(0)

if __name__ == "__main__":
    print("=== Reddit Bot Starting ===")
    print("Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    monitor_reddit()