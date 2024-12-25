import re
import time
from datetime import datetime

def parse_time_string(time_str):
    """Convert time string to seconds"""
    time_units = {
        'ms': 0.001,
        's': 1,
        'm': 60,
        'h': 3600,
    }
    parts = re.findall(r'(\d+)([a-z]+)', time_str.lower())
    return sum(float(value) * time_units[unit] for value, unit in parts)

def format_time_remaining(seconds):
    """Format seconds into a readable time string"""
    if seconds < 0:
        return "0s"  # Handle negative seconds gracefully
    if seconds < 60:
        return f"{int(seconds)}s"  # Cast to int for precision
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
