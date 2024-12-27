import time

def format_time_remaining(seconds):
    """Format seconds into a readable time string"""
    if seconds < 0:
        return "0s"
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)}m {int(remaining_seconds)}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"

def format_time_until(future_timestamp):
    """Format time remaining until a future timestamp"""
    remaining = max(0, future_timestamp - time.time())
    if remaining < 60:
        return f"{int(remaining)} seconds"
    else:
        return f"{int(remaining/60)} minutes, {int(remaining%60)} seconds"

def sleep_with_check(seconds, check_interval=0.1):
    """Sleep for specified duration while allowing interrupts"""
    end_time = time.time() + seconds
    while time.time() < end_time:
        time.sleep(min(check_interval, end_time - time.time()))
