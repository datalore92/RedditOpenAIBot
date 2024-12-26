import time
import curses
import threading
import queue
from datetime import datetime
from .config import SUBREDDITS, KEYWORDS
from .reddit_handler import reddit, process_submission, check_tracked_threads, thread_tracker
from .utils import format_time_until, format_time_remaining
from .reddit_handler import thread_tracker_lock

MAX_LOG_LINES = 100  # Maximum number of log messages to keep

# Configuration Variable
USE_CURSES = False  # Disable curses interface in container

# Log File Configuration
LOG_FILE = '/app/logs/bot.log'  # Path to the log file

def run_curses_interface(stdscr, log_queue):
    try:
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(500)  # Refresh every 500ms
        max_y, max_x = stdscr.getmaxyx()

        # Initialize color pairs
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)      # For errors
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # For warnings
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)    # For normal logs

        log_buffer = []

        # Add error handling for log display
        def safe_addstr(y, x, string, *args):
            try:
                if y < max_y and x < max_x:
                    # Truncate string to fit window
                    available_width = max_x - x
                    if len(string) > available_width:
                        string = string[:available_width-3] + "..."
                    stdscr.addstr(y, x, string, *args)
            except curses.error:
                pass

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "=== Bot Curses UI ===")
            stdscr.addstr(1, 0, "Tracked Threads:")

            # Acquire the lock before accessing thread_tracker
            with thread_tracker_lock:
                tracked_threads = [item for item in thread_tracker.items() if not item[1].replied_to_op]

            # Define per-thread display width
            thread_display_width = 40  # Adjust based on content

            # Calculate how many threads can fit per row
            threads_per_row = max_x // thread_display_width
            if threads_per_row == 0:
                threads_per_row = 1  # Ensure at least one thread per row

            # Initialize `row` before the loop to ensure it's always defined
            row = 2

            # Display each tracked thread in a grid layout
            for index, (submission_id, state) in enumerate(tracked_threads):
                time_left = max(0, int(state.op_reply_time - time.time()))
                timer_str = format_time_remaining(time_left)
                display_str = f"ID: {submission_id[:8]}... - Timer: {timer_str}"

                # Calculate row and column positions
                display_row = row + (index // threads_per_row) * 2  # Multiply by 2 for spacing between rows
                display_col = (index % threads_per_row) * thread_display_width

                # Handle potential string length exceeding allocated width
                if len(display_str) > thread_display_width - 2:
                    display_str = display_str[:thread_display_width - 5] + "..."

                try:
                    stdscr.addstr(display_row, display_col, display_str)
                except curses.error:
                    pass  # Ignore if trying to write outside the window

            # Update `log_row` based on the number of active threads
            log_row = row + ((len(tracked_threads) - 1) // threads_per_row) * 2 + 2

            # Display log messages
            stdscr.addstr(log_row, 0, "Logs:")
            log_row += 1

            # Retrieve all log messages from the queue
            while not log_queue.empty():
                try:
                    log_message = log_queue.get_nowait()
                    if len(log_buffer) >= MAX_LOG_LINES:
                        log_buffer.pop(0)  # Remove oldest message
                    log_buffer.append(log_message)
                except queue.Empty:
                    break

            # Display log buffer
            start_log = max(0, len(log_buffer) - (max_y - log_row - 2))
            for msg in log_buffer[start_log:]:
                if "✗" in msg:
                    stdscr.attron(curses.color_pair(1))
                    safe_addstr(log_row, 0, msg[:max_x-1])
                    stdscr.attroff(curses.color_pair(1))
                elif "⚠️" in msg:
                    stdscr.attron(curses.color_pair(2))
                    safe_addstr(log_row, 0, msg[:max_x-1])
                    stdscr.attroff(curses.color_pair(2))
                else:
                    stdscr.attron(curses.color_pair(3))
                    safe_addstr(log_row, 0, msg[:max_x-1])
                    stdscr.attroff(curses.color_pair(3))
                log_row += 1
                if log_row >= max_y - 1:
                    break

            stdscr.addstr(max_y-1, 0, "Press 'q' to quit.")
            
            stdscr.refresh()

            # Check for user exit
            try:
                key = stdscr.getch()
                if key == ord('q'):
                    break
            except:
                pass

            time.sleep(0.1)
    except KeyboardInterrupt:
        return
    except Exception as e:
        print(f"Curses error: {e}")
        return

def logger(log_queue, message):
    """Enqueue log messages and write them to a log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    # Write to console
    print(formatted_message)
    
    # Write to log file
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(formatted_message + "\n")
            f.flush()  # Force write to disk
    except Exception as e:
        print(f"Error writing to log file: {e}")
    
    # Enqueue for UI if needed
    log_queue.put(formatted_message)

def monitor_reddit_process(log_queue):
    """Monitor Reddit and process submissions."""
    try:
        logger(log_queue, "✓ Monitoring subreddits: " + ", ".join(SUBREDDITS))
        if KEYWORDS:
            logger(log_queue, "✓ Looking for keywords: " + ", ".join(KEYWORDS))
        else:
            logger(log_queue, "✓ No keywords set - will reply to all posts")
        logger(log_queue, f"Bot authenticated as: u/{reddit.user.me().name}")
        
        logger(log_queue, "Monitoring for new posts...")
        
        while True:
            try:
                # Always process tracked threads first
                check_tracked_threads(logger_wrapper(log_queue))
                
                # **Modify the stream to include pause_after**
                subreddit = reddit.subreddit('+'.join(SUBREDDITS))
                for submission in subreddit.stream.submissions(skip_existing=True, pause_after=0):
                    if submission:
                        process_submission(submission, log=logger_wrapper(log_queue))  # Ensure log is passed correctly
                    # Always check tracked threads, even if no new submission
                    check_tracked_threads(logger_wrapper(log_queue))
                    
                # **Sleep briefly to prevent tight loop when no submissions**
                time.sleep(0.1)
                    
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger(log_queue, f"✗ Error in monitoring loop: {e}")
                time.sleep(1)  # Increased retry time for stability
                continue
    
    except KeyboardInterrupt:
        logger(log_queue, "Bot shutdown requested. Shutting down gracefully...")
    finally:
        logger(log_queue, "Bot stopped successfully.")

def logger_wrapper(log_queue):
    """Wrap the logger to pass the log queue."""
    def log(message, *args):
        if args:
            try:
                message = message % args
            except TypeError as e:
                # Handle formatting errors
                logger(log_queue, f"✗ Log formatting error: {e}")
                return
        logger(log_queue, message)
    # Ensure that a callable is returned
    assert callable(log), "logger_wrapper did not return a callable log function."
    return log

def check_tracked_threads(log):
    """Check all tracked threads for new comments and OP replies"""
    # ...existing code...

    for submission_id, state in list(thread_tracker.items()):
        try:
            submission = reddit.submission(id=submission_id)
            submission.comments.replace_more(limit=0)  # Refresh comments
            
            # **Handle replies in separate threads**
            reply_thread = threading.Thread(target=process_submission, args=(submission, state, False, log))
            reply_thread.start()
            
        except Exception as e:
            log("✗ Error checking thread %s: %s", submission_id, str(e))
            continue

def monitor_reddit_curses(log_queue):
    """Start the curses interface."""
    curses.wrapper(run_curses_interface, log_queue)

def monitor_reddit_standard(log_queue):
    """Monitor Reddit with standard logging (without curses)."""
    try:
        logger(log_queue, "✓ Monitoring subreddits: " + ", ".join(SUBREDDITS))
        if KEYWORDS:
            logger(log_queue, "✓ Looking for keywords: " + ", ".join(KEYWORDS))
        else:
            logger(log_queue, "✓ No keywords set - will reply to all posts")
        logger(log_queue, f"Bot authenticated as: u/{reddit.user.me().name}")
        
        logger(log_queue, "Monitoring for new posts...")
        
        while True:
            try:
                # Always process tracked threads first
                check_tracked_threads(logger_wrapper(log_queue))
                
                # Brief pause to avoid hammering the API
                time.sleep(0.5)
                
                # Monitor new submissions
                subreddit = reddit.subreddit('+'.join(SUBREDDITS))
                for submission in subreddit.stream.submissions(skip_existing=True):
                    process_submission(submission, log=logger_wrapper(log_queue))
                    # Immediately check if any threads need replies
                    check_tracked_threads(logger_wrapper(log_queue))
                    
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger(log_queue, f"✗ Error in monitoring loop: {e}")
                time.sleep(5)  # Shorter retry time
                continue
    
    except KeyboardInterrupt:
        logger(log_queue, "Bot shutdown requested. Shutting down gracefully...")
    finally:
        logger(log_queue, "Bot stopped successfully.")

def monitor_reddit_standard_mode():
    """Monitor Reddit in standard logging mode without curses."""
    # Initialize log queue
    log_queue = queue.Queue()
    
    # Get the log function
    log = logger_wrapper(log_queue)
    assert callable(log), "Log function is not callable."
    
    # Start Reddit monitoring in the main thread
    monitor_reddit_standard(log_queue)

def monitor_reddit_curses_mode():
    """Monitor Reddit with curses interface."""
    # Initialize log queue
    log_queue = queue.Queue()
    
    # Get the log function
    log = logger_wrapper(log_queue)
    assert callable(log), "Log function is not callable."
    
    # Start Reddit monitoring in a separate thread
    reddit_thread = threading.Thread(target=monitor_reddit_process, args=(log_queue,), daemon=True)
    reddit_thread.start()
    
    # Start curses interface
    monitor_reddit_curses(log_queue)

if __name__ == "__main__":
    print("=== Reddit Solana Bot Starting ===")
    print("Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    if USE_CURSES:
        monitor_reddit_curses_mode()
    else:
        monitor_reddit_standard_mode()