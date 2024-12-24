import re
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
    """Format seconds into readable time"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
