import re
from collections.abc import Callable

from app.schemas.privacy import RedactionResult

SLMFallback = Callable[[str], str]

# Ordered so already-redacted spans can't be re-matched by a later, broader pattern.
_PATTERNS: dict[str, re.Pattern[str]] = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "student_id": re.compile(r"\bSTU-\d{6}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){12,15}\d\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
}


class PrivacySanitizerAgent:
    """Intercepts raw logs, tickets, and user prompts before they reach a cloud LLM.

    Regex handles well-known FERPA/PCI identifiers (SSNs, credit card numbers,
    student IDs, personal emails) deterministically. An optional SLM fallback
    then runs over the already-redacted text to catch identifiers regex can't
    reliably match (e.g. names or addresses in free text). The fallback
    defaults to a no-op passthrough so the agent works without a local model
    wired up; pass a callable (e.g. a local SLM inference call) to enable it.
    """

    def __init__(self, slm_fallback: SLMFallback | None = None):
        self._slm_fallback = slm_fallback or (lambda text: text)

    def sanitize(self, text: str) -> RedactionResult:
        redacted = text
        counts: dict[str, int] = {}

        for label, pattern in _PATTERNS.items():
            redacted, count = pattern.subn(f"[REDACTED_{label.upper()}]", redacted)
            if count:
                counts[label] = count

        redacted = self._slm_fallback(redacted)

        return RedactionResult(original=text, redacted=redacted, redaction_counts=counts)
