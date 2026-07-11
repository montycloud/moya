# Memory

MOYA's memory system stores conversation history as **threads** of **messages**. The storage backend is pluggable — swap `InMemoryRepository` for `FileSystemRepository` (or your own implementation) without changing any agent code.

---

## Core Model

A **Thread** is an ordered list of **Messages** identified by a `thread_id`. Agents use the thread to provide conversation context to the LLM on each turn.

```
Thread (thread_id="session-42")
├── Message(sender="user",      content="My name is Alice.")
├── Message(sender="assistant", content="Nice to meet you, Alice!")
├── Message(sender="user",      content="What is my name?")
└── Message(sender="assistant", content="Your name is Alice.")
```

---

## Repository Pattern

`Repository` is an abstract base class. All storage operations go through this interface:

```python
from moya.memory.repository import Repository

class Repository:
    def create_thread(self, thread: Thread) -> None: ...
    def get_thread(self, thread_id: str) -> Optional[Thread]: ...
    def append_message(self, thread_id: str, message: Message) -> None: ...
    def list_threads(self) -> List[str]: ...
    def delete_thread(self, thread_id: str) -> None: ...
```

### InMemoryRepository

Default. Stores everything in a Python dict. State is lost when the process exits.

```python
from moya import InMemoryRepository

repo = InMemoryRepository()
```

### FileSystemRepository

Stores each thread as a JSON file in a directory. State persists across restarts.

```python
from moya import FileSystemRepository

repo = FileSystemRepository(base_path="./conversation_history")
```

Files are named `{base_path}/{thread_id}.json`.

### Custom backend

Implement `Repository` to use any store (Redis, DynamoDB, PostgreSQL, …):

```python
from moya.memory.repository import Repository
from moya.conversation.thread import Thread
from moya.conversation.message import Message

class RedisRepository(Repository):
    def __init__(self, client):
        self._r = client

    def create_thread(self, thread: Thread) -> None:
        self._r.set(f"thread:{thread.thread_id}", json.dumps({"messages": []}))

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        raw = self._r.get(f"thread:{thread_id}")
        if raw is None:
            return None
        # deserialise and return Thread object
        ...

    # implement remaining methods
```

---

## Using Memory with Agents

Pass any `Repository` instance to `create_agent()`:

```python
from moya import create_agent, InMemoryRepository

memory = InMemoryRepository()
agent = create_agent("openai", name="bot", description="Chat bot", memory=memory)

# Pass thread_id on every call to use the same conversation thread
agent.handle_message("My name is Alice.", thread_id="session-1")
response = agent.handle_message("What is my name?", thread_id="session-1")
print(response)  # → "Your name is Alice."
```

The agent automatically:
1. Loads the thread from the repository before each LLM call.
2. Appends user message + assistant response after each successful call (`_remember()`).

Different `thread_id` values create isolated conversations:

```python
agent.handle_message("I am Alice.", thread_id="alice")
agent.handle_message("I am Bob.",   thread_id="bob")

# These are separate conversations
agent.handle_message("Who am I?", thread_id="alice")  # → "You are Alice."
agent.handle_message("Who am I?", thread_id="bob")    # → "You are Bob."
```

---

## EphemeralMemory

`EphemeralMemory` is a convenience wrapper that exposes memory operations as **tools** the LLM can call. This is useful when you want the agent to decide what to remember rather than always persisting every message.

```python
from moya import create_agent, ToolRegistry
from moya.tools.ephemeral_memory import EphemeralMemory

registry = ToolRegistry()
em = EphemeralMemory()
em.configure_memory_tools(registry)
# Registers three tools into registry:
#   store_message(thread_id, sender, content)
#   get_last_n_messages(thread_id, n=5)
#   get_thread_summary(thread_id)

agent = create_agent("openai", name="bot", description="...", tool_registry=registry)
```

Each `EphemeralMemory` instance has its own isolated `InMemoryRepository`. Two instances never share state, even if they use the same `thread_id`.

---

## Conversation API on Agent

Agents expose two convenience methods for reading conversation history:

```python
# Last N messages as a list
messages = agent.get_last_n_messages("session-1", n=10)

# Full thread summary as a string
summary = agent.get_conversation_summary("session-1")
```

---

## Thread and Message Models

### Thread

```python
from moya.conversation.thread import Thread

thread = Thread(
    thread_id="session-1",
    participants=["user", "assistant"],  # optional
    metadata={"user_timezone": "UTC"},   # optional
)

thread.add_message(message)
messages = thread.get_messages()
recent = thread.get_last_n_messages(n=5)
```

### Message

```python
from moya.conversation.message import Message

msg = Message(
    thread_id="session-1",
    sender="user",           # "user", "assistant", or agent name
    content="Hello!",
    metadata={"role": "user"},   # optional
)

d = msg.to_dict()  # JSON-serialisable dict
```
