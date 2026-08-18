from dataclasses import dataclass, field


@dataclass
class RedactionResult:
    original: str
    redacted: str
    redaction_counts: dict[str, int] = field(default_factory=dict)
