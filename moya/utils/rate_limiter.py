from time import time
from collections import deque
from typing import Deque
from dataclasses import dataclass, field

@dataclass
class RateLimiter:
    max_requests: int # max requests
    time_window: float  # in seconds
    requests: Deque[float] = field(default_factory=deque)
    
    def can_proceed(self) -> bool:
        current_time = time()
        
        # removes old timestamps
        while self.requests and current_time - self.requests[0] > self.time_window:
            self.requests.popleft()
            
        if len(self.requests) < self.max_requests:
            self.requests.append(current_time)
            return True
            
        return False
