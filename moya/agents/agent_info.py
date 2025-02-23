from dataclasses import dataclass


@dataclass
class AgentInfo():
    "A class that holds information about an agent"
    name: str
    description: str
    type: str

    def __init__(self, name: str, description: str, type: str):
        self.name = name
        self.description = description
        self.type = type
