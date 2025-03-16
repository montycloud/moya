import pytest
import time
from moya.agents.base_agent import Agent, AgentConfig

class TestAgent(Agent):
    def _handle_message_impl(self, message: str, **kwargs) -> str:
        time.sleep(0.1)  # processing time ( as this is still a work in development)
        if message == "fail":
            raise ValueError("Test failure")
        return f"Processed: {message}"

@pytest.fixture
def test_agent():
    config = AgentConfig(
        agent_name="test_agent",
        agent_type="test",
        description="Test agent",
        rate_limit_max_requests=2,
        rate_limit_window=1.0
    )
    return TestAgent(config)

def test_rate_limiting(test_agent):
    # these both should work
    assert test_agent.handle_message("test1") == "Processed: test1"
    assert test_agent.handle_message("test2") == "Processed: test2"
    
    # this one should fail
    with pytest.raises(RuntimeError, match="Rate limit exceeded"):
        test_agent.handle_message("test3")
        
    # rate limit goes now
    time.sleep(1.1)
    
    # test4 also should work
    assert test_agent.handle_message("test4") == "Processed: test4"

def test_health_monitoring(test_agent):
    # Successful 
    test_agent.handle_message("test")
    
    # Failed 
    with pytest.raises(ValueError):
        test_agent.handle_message("fail")
        
    # stats
    metrics = test_agent.get_health_metrics()
    assert metrics["total_requests"] == 2
    assert metrics["successful_requests"] == 1
    assert metrics["failed_requests"] == 1
    assert 0 < metrics["average_response_time"] < 1.0
    assert "Test failure" in metrics["last_error"]

def test_stress(test_agent):
    # higher rate limit test
    config = AgentConfig(
        agent_name="stress_agent",
        agent_type="test",
        description="Test agent",
        rate_limit_max_requests=100,
        rate_limit_window=1.0
    )
    stress_agent = TestAgent(config)
    
    # fast testing
    for i in range(50):
        stress_agent.handle_message(f"message{i}")
        
    metrics = stress_agent.get_health_metrics()
    assert metrics["total_requests"] == 50
    assert metrics["successful_requests"] == 50
    assert metrics["failed_requests"] == 0
    assert metrics["average_response_time"] > 0
