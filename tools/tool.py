"""A tool is a named Python function the agent may ask the harness to run."""
from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[..., dict]
    type: str = "function"   # OTel value for gen_ai.tool.type: function, extension or datastore
