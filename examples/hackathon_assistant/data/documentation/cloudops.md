# CloudOps Integration Guide

## Overview

Moya provides robust integration with cloud services through specialized agents and tools, enabling automated cloud operations and management.

## Core Capabilities

### 1. Resource Management
- EC2 instance monitoring and control
- S3 bucket operations
- RDS database management
- Lambda function deployment
- Container orchestration

### 2. Security & Compliance
- IAM policy management
- Security group configuration
- Compliance checking
- Audit log analysis
- Vulnerability scanning

### 3. Cost Optimization
- Resource utilization analysis
- Cost forecasting
- Idle resource detection
- Right-sizing recommendations
- Budget management

## Implementation Guide

### Setting Up Cloud Access

1. AWS Configuration:
```python
from moya.tools import AWSCloudTool
from moya.agents import BedrockAgent

# Configure AWS access
aws_tool = AWSCloudTool(
    profile="prod",
    region="us-east-1",
    assume_role_arn="arn:aws:iam::123456789012:role/CloudOpsRole"
)
```

2. Multi-Cloud Setup:
```python
from moya.tools import AzureCloudTool, GCPCloudTool

# Configure multiple cloud providers
azure_tool = AzureCloudTool(subscription_id="sub-id")
gcp_tool = GCPCloudTool(project_id="project-id")
```

### Creating Cloud-Aware Agents

1. Single Cloud Agent:
```python
# Create AWS-focused agent
aws_agent = BedrockAgent(
    agent_name="aws_ops",
    description="AWS resource management specialist",
    system_prompt="""You are an AWS operations specialist. 
    Your role is to manage and optimize AWS resources.""",
    tool_registry=tool_registry
)

# Register cloud tools
tool_registry.register_tool(aws_tool)
```

2. Multi-Cloud Orchestration:
```python
# Create cloud-specific agents
aws_agent = BedrockAgent(name="aws_ops")
azure_agent = OpenAIAgent(name="azure_ops")
gcp_agent = OpenAIAgent(name="gcp_ops")

# Set up orchestration
registry = AgentRegistry()
registry.register_agents([aws_agent, azure_agent, gcp_agent])

orchestrator = MultiAgentOrchestrator(
    agent_registry=registry,
    classifier=classifier
)
```

## Common Operations

### Resource Health Monitoring
```python
# Check EC2 instance health
response = agent.handle_message(
    "Check health of all EC2 instances in prod environment"
)

# Monitor RDS databases
response = agent.handle_message(
    "Get performance metrics for RDS instances"
)
```

### Cost Management
```python
# Get cost analysis
response = agent.handle_message(
    "Analyze last month's AWS costs and suggest optimizations"
)

# Find idle resources
response = agent.handle_message(
    "Identify unused EC2 instances and EBS volumes"
)
```

### Security Operations
```python
# Security audit
response = agent.handle_message(
    "Audit IAM roles and identify overprivileged accounts"
)

# Compliance check
response = agent.handle_message(
    "Check if S3 buckets comply with security policies"
)
```

## Best Practices

### 1. Access Management
- Use IAM roles with least privilege
- Rotate credentials regularly
- Enable MFA for critical operations
- Use separate roles for different environments

### 2. Error Handling
```python
try:
    response = aws_agent.handle_message("restart-ec2-instance-i-1234567")
except CloudOperationError as e:
    logging.error(f"Cloud operation failed: {e}")
    # Implement retry or fallback logic
```

### 3. Monitoring and Logging
```python
# Enable detailed logging
aws_tool.enable_cloudwatch_logging()

# Set up monitoring
aws_tool.configure_monitoring(
    metrics=["CPU", "Memory", "Network"],
    alert_threshold=80
)
```

### 4. Cost Controls
- Set up budget alerts
- Implement auto-scaling policies
- Schedule resource cleanup
- Use spot instances where appropriate

## Integration Examples

### 1. Automated Incident Response
```python
@incident_handler
def handle_high_cpu_alert(incident):
    # Create incident response agent
    responder = BedrockAgent(
        name="incident_response",
        system_prompt="You are an incident response specialist..."
    )
    
    # Handle the incident
    response = responder.handle_message(
        f"Investigate high CPU usage in {incident.resource_id}"
    )
```

### 2. Resource Optimization
```python
@daily_task
def optimize_resources():
    # Create optimization agent
    optimizer = BedrockAgent(
        name="resource_optimizer",
        system_prompt="You are a cloud resource optimization specialist..."
    )
    
    # Run optimization
    response = optimizer.handle_message(
        "Analyze and optimize all production resources"
    )
```

### 3. Compliance Automation
```python
@compliance_check
def verify_compliance():
    # Create compliance agent
    auditor = BedrockAgent(
        name="compliance_auditor",
        system_prompt="You are a security compliance specialist..."
    )
    
    # Run compliance check
    response = auditor.handle_message(
        "Verify compliance with security policies"
    )
```