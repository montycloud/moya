from dataclasses import dataclass, field
from typing import Dict, Any
from time import time

@dataclass
class HealthMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_error: str = ""
    last_check: float = field(default_factory=time)

class AgentHealthMonitor:
    def __init__(self):
        self.metrics = HealthMetrics()
        
    def record_request(self, success: bool, response_time: float, error: str = ""):
        self.metrics.total_requests += 1
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
            self.metrics.last_error = error
            
        self.metrics.average_response_time = (
            (self.metrics.average_response_time * (self.metrics.total_requests - 1) + response_time) 
            / self.metrics.total_requests
        )
        self.metrics.last_check = time()
        
    def get_metrics(self) -> Dict[str, Any]:
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "average_response_time": round(self.metrics.average_response_time, 2),
            "success_rate": round(self.metrics.successful_requests / max(self.metrics.total_requests, 1) * 100, 2),
            "last_error": self.metrics.last_error,
            "last_check": self.metrics.last_check
        }
