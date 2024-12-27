from datetime import datetime

class BotLogger:
    def __init__(self, log_file_path):
        self.log_file = log_file_path
    
    def log(self, message, *args):
        """Format and log a message"""
        try:
            if args:
                message = message % args
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            
            # Write to console
            print(formatted_message)
            
            # Write to file
            with open(self.log_file, 'a') as f:
                f.write(formatted_message + "\n")
                f.flush()
                
        except Exception as e:
            print(f"Logging error: {e}")
