# File: result.py
# Location: project_root/models/result.py

from dataclasses import dataclass
from typing import Any, Dict
from swarm import Agent

@dataclass
class Result:
    value: Any
    context_variables: Dict[str, Any] = None
    agent: Agent = None