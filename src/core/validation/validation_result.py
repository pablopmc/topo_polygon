from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ValidationLevel(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

@dataclass
class ValidationMessage:
    level: ValidationLevel
    message: str
    vertex_index: Optional[int] = None
    field: Optional[str] = None

@dataclass
class ValidationResult:
    messages: list[ValidationMessage]

    @property
    def has_errors(self) -> bool:
        return any(msg.level == ValidationLevel.ERROR for msg in self.messages)
