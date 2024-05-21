from typing import Optional, Sequence

from dataclasses import dataclass


@dataclass
class AgentAnswer:
    message: str
    documents: Optional[Sequence[str]] = None
