import time
import threading
from ..config import REPLY_WAIT_TIME

class ThreadState:
    def __init__(self, submission):
        self.submission = submission
        self.replied_to_op = False
        self.op_reply_time = time.time() + REPLY_WAIT_TIME
        self.waiting_for_op_responses = True
        self.responded_to_comments = set()
        self.first_comment_logged = False
        self.has_replied_to_comment = False  # Add this flag

    @property
    def is_complete(self):
        # Thread is complete when we've replied to OP and one comment
        return self.replied_to_op and self.has_replied_to_comment

# Global state management
thread_tracker = {}
thread_tracker_lock = threading.Lock()
