"""
Interactive chat example using OpenAI agent with conversation memory.
"""

import os

from moya.tools.tool_registry import ToolRegistry
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.tools.ephemeral_memory import EphemeralMemory
from moya.vectorstore.chroma_vectorstore import ChromaVectorStore
import os
import json
from examples.quick_tools import QuickTools
from moya.tools.base_tool import BaseTool
from moya.tools.rag_tool import RAGTool
import boto3


def get_embedding(text):
    client = boto3.client(service_name='bedrock-runtime',
                          region_name='us-west-2')

    response = client.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps(
            {'inputText': text}
        ),
        contentType='application/json',
        accept='application/json'
    )
    # Parse the response (usually, embeddings are in 'body' or 'predictions')
    response_body = json.loads(
        response['body'].read().decode('utf-8'))['embedding']
    return response_body


def setup_rag_tool():
    """
    Set up the RAGTool with a vector store and return the tool instance.
    """

    data = [
        {
            "id": "0",
            "metadata": {
                "month": "January",
            },
            "document": """January 10th
Customer:
Hey Copilot, I'm drowning in AWS alerts. Finance says our spend jumped 30% last month. Can you figure out why?

Copilot:
Hi Sarah! Let's dig in. One sec…
Analyzing cost drivers…
Spike Detected: $4,200 increase in AWS US-East-1.
Breakdown:

$2,800 from 12 t3.xlarge EC2 instances running 24/7 (tagged Environment: Staging).

$1,100 from unmonitored S3 storage in s3://backup-old.

$300 from idle RDS instances.

These staging instances haven't been used in 14 days. Want me to:

Stop them and automate a schedule?

Delete the old backups?

Customer:
Stop the instances, but don't delete anything yet. Let me check with the dev team first.

Copilot:
Got it! Stopping instances now. I'll send a Slack reminder to @dev-team to confirm deletion.
Heads up: The s3://backup-old bucket isn't encrypted. Want me to enable that?

Customer:
Yes, encrypt it. And can you auto-apply encryption for new buckets?

Copilot:
Done! New S3 buckets will now default to AES-256 encryption. I'll alert you if anyone overrides this."""
        },
        {
            "id": "1",
            "metadata": {
                "month": "February",
            },
            "document": """February 5th
Customer:
Copilot, got an email about a "public S3 bucket." What's that about?

Copilot:
Hi Sarah! Let me pull details…
Incident Summary:

Bucket s3://client-uploads-2024 was set to public via a misconfigured Terraform script.

Exposed Data: 1,240 files (including client_invoices/).

Action Taken: Restricted to private, notified owner:marketing@company.com.

Want me to:

Run a full audit of all buckets?

Block public access org-wide?

Customer:
Block public access everywhere. And send the audit report to my team.

Copilot:
Org-wide public access blocked.
Audit Results:

3 buckets had public read access (now fixed).

7 buckets had outdated ACLs (migrated to bucket policies).

Report sent to cloud-ops@company.com."""
        },
        {
            "id": "2",
            "metadata": {
                "month": "March", },
            "document": """March 15th
Customer:
Copilot, the CISO is asking about compliance. How's our AWS setup doing?

Copilot:
Hi Sarah! Let's review:
AWS Well-Architected Score: 92% (up from 74% in Jan).
Remaining Issues:

2 IAM roles with admin privileges unused for 90+ days.

1 unpatched RDS instance (MySQL 5.7, critical CVE).

I can:

Delete the stale IAM roles.

Patch RDS during the next maintenance window (March 20th, 2 AM).

Customer:
Delete the roles and schedule the patch. Any downtime expected?

Copilot:
Roles deleted. Patching will cause 10 mins of downtime. I'll send a reminder to @dev-ops and retry if it fails.

Customer:
Perfect. Oh, and what's this "sustainability dashboard" alert?

Copilot:
Sustainability Update:

Your carbon footprint dropped 22% this month!

Why? Migrating 15 EC2 instances to Graviton + deleting 8 TB of old snapshots.

Want to include this in your exec report? I can generate a one-pager.

Customer:
Yes! Add a comparison to last quarter.

Copilot:
On it! Drafting now."""
        },
        {
            "id": "3",
            "metadata": {
                "month": "April", },
            "document": """April 3rd
Customer:
Copilot, Team A says their "dev-analytics" cluster is missing. Did something happen?

Copilot:
Let me check…
Activity Logs:

The cluster (env:dev-analytics) was auto-stopped on April 1st due to the 7 PM–7 AM schedule.

Action: Restarted it now. Should I exclude this cluster from the schedule?

Customer:
Yes, they need 24/7 access. Why is it stopped?

Copilot:
Back in January, we set a schedule to reduce idle costs. Since dev-analytics is now active at night, I'll remove it from automation.

Customer:
Thanks. Also, I need a list of all resources tagged "Project: Phoenix" for an audit.

Copilot:
Compiling…
Project: Phoenix:

EC2: 8 instances (4 running, 4 stopped).

S3: s3://phoenix-raw-data (12 TB, encrypted).

RDS: phoenix-db (PostgreSQL 14, 90% CPU avg).

The RDS instance is overutilized. Want to upgrade it to a larger tier?

Customer:
Not yet. Just flag it for the eng team.

Copilot:
Added to team-eng's Jira backlog. They'll get a priority alert."""
        },
        {
            "id": "4",
            "metadata": {
                "month": "May", },
            "document": """May 8th
Customer:
Copilot, we're seeing latency spikes in our production API. Could this be related to those EC2 changes we made last month?

Copilot:
Checking metrics...
Analysis complete:

API latency increased by 300ms on average since April 28th.

Correlation detected: The api-prod auto-scaling group hasn't scaled up during peak traffic (current max instances: 8, recommended: 12).

Root cause: CPU threshold for scaling was set too high (90%, should be 70%).

I can:

Adjust the scaling policy immediately

Schedule a load test to validate new thresholds

Customer:
Do both. But run the load test after hours - say 10 PM tonight.

Copilot:
Policy updated (now scales at 70% CPU). Load test scheduled for 10 PM. I'll notify you and @platform-team of results."""
        },
        {
            "id": "5",
            "metadata": {
                "month": "June", },
            "document": """June 12th
Customer:
The security team wants to implement new CIS benchmarks. How far are we from compliance?

Copilot:
Compliance assessment running...
Current status vs CIS AWS v1.4:

87% compliant (was 72% in March)

Critical gaps:

CloudTrail not enabled in all regions (3/5 regions missing)

No MFA requirement for IAM users with console access (12 users affected)

S3 versioning disabled on 4/15 production buckets

Recommended action plan ready. Should I:

Automatically remediate non-breaking items?

Schedule a change advisory board review first?

Customer:
Fix the CloudTrail and S3 issues automatically. Hold on MFA changes - we need to communicate that first.

Copilot:
Enabling CloudTrail globally and activating S3 versioning now. Drafted comms for MFA rollout - want to review before sending to @all-employees?"""
        },
        {
            "id": "6",
            "metadata": {
                "month": "July", },
            "document": """July 19th
Customer:
We're getting Azure cost alerts again. What changed?

Copilot:
Cost anomaly detected:

$3,800 overspend in Azure West Europe

Primary driver: 4 new Standard_D8s_v3 VMs running continuously for 17 days (tagged Project:BlueMoon)

Secondary factor: 45TB of hot storage in bluemoon-raw container

These resources aren't covered by our existing policies. Options:

Extend cost controls to new subscription

Contact owner:research-team@company.com for clarification

Customer:
Reach out to the research team first. If no response in 24h, auto-apply our standard dev/test policies.

Copilot:
Email sent to research team lead. Fallback policy will activate tomorrow at 3 PM if unclaimed."""
        },
        {
            "id": "7",
            "metadata": {
                "month": "August", },
            "document": """August 3rd
Customer:
Copilot, prepare a migration readiness report for our AWS to GCP project.

Copilot:
Migration assessment generated:
Inventory Summary:

142 AWS resources tagged MigrationTarget:GCP

Compatibility breakdown:

89% direct equivalent services

8% require refactoring (mainly RDS PostgreSQL → Cloud SQL)

3% no GCP equivalent (AWS-specific services)

Risk Analysis:

High: 3 legacy apps using DynamoDB streams

Medium: IAM policy translation for 45 custom roles

Low: Storage class conversions

Want me to:

Schedule a planning session with @cloud-migration-team?

Generate Terraform conversion templates?

Customer:
Both. Start with the high-risk items first.

Copilot:
Scheduled meeting for August 7th. Initial Terraform templates for the DynamoDB workloads will be ready by EOD tomorrow."""
        }
    ]

    vectordb = ChromaVectorStore(
        path="./chroma_db", collection_name="conversations", embedding_function=get_embedding)
    # vectordb.add_vectors(data)
    rag_tool = RAGTool(vectordb=vectordb)
    return rag_tool


def setup_agent():
    tool_registry = ToolRegistry()
    EphemeralMemory.configure_memory_tools(tool_registry)
    tool_registry.register_tool(BaseTool(
        name="ConversationContext", function=QuickTools.get_conversation_context))

    # rag_tool = setup_rag_tool()
    # rag_tool.configure_tool_registry(tool_registry)

    config = OpenAIAgentConfig(
        agent_name="chat_agent",
        description="An interactive chat agent",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o",
        agent_type="ChatAgent",
        tool_registry=tool_registry,
        is_streaming=True,
        system_prompt="You are an interactive chat agent that can remember previous conversations. "
                      "You have access to tools that helps you to store and retrieve conversation history. The tools are: "
        "1. ConversationContext: Use this tool to get the conversation context."
        "2. RAGTool: Use this tool to search for information about the AWS account."
                      "Use the conversation history for your reference in answering any ueser query."
                      "Be Helpful and polite in your responses, and be concise and clear."
                      "Be useful but do not provide any information unless asked.",
    )

    # Create OpenAI agent with memory capabilities
    agent = OpenAIAgent(config)

    # Set up registry and orchestrator
    agent_registry = AgentRegistry()
    agent_registry.register_agent(agent)
    orchestrator = SimpleOrchestrator(
        agent_registry=agent_registry,
        default_agent_name="chat_agent"
    )

    return orchestrator, agent


def format_conversation_context(messages):
    context = "\nPrevious conversation:\n"
    for msg in messages:
        # Access Message object attributes properly using dot notation
        sender = "User" if msg.sender == "user" else "Assistant"
        context += f"{sender}: {msg.content}\n"
    return context


def main():
    orchestrator, agent = setup_agent()
    thread_id = json.loads(QuickTools.get_conversation_context())["thread_id"]

    print("Welcome to Interactive Chat! (Type 'quit' or 'exit' to end)")
    print("-" * 50)

    while True:
        # Get user input
        user_input = input("\nYou: ").strip()

        # Check for exit command
        if user_input.lower() in ['quit', 'exit']:
            print("\nGoodbye!")
            break

        # Store user message
        EphemeralMemory.store_message(
            thread_id=thread_id, sender="user", content=user_input)

        # Search for relevant documents using RAGTool
        rag_tool = setup_rag_tool()
        search_results = rag_tool.search_documents(query_text=user_input)

        # Format search results for context
        search_context = "\n".join(
            [f"Document {i+1}: {result['content']}" for i, result in enumerate(search_results)]
        )

        # Combine search results with user input
        enriched_input = f"Search Context:\n{search_context}\n\nUser Query: {user_input}"

        # Store the assistant's response
        print("\nAssistant: ", end="", flush=True)

        # Define callback for streaming
        def stream_callback(chunk):
            print(chunk, end="", flush=True)

        # Get response using stream_callback
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enriched_input,
            stream_callback=stream_callback
        )

        EphemeralMemory.store_message(
            thread_id=thread_id, sender="assistant", content=response)
        print()


if __name__ == "__main__":
    main()
