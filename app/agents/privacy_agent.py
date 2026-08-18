import re
from typing import Optional

# Regex-based patterns for common sensitive data
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CC_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
STU_RE = re.compile(r"\bSTU-\d{6}\b", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")

def redact(text: str) -> str:
    """Deterministic redaction pass using regexes. Returns redacted text."""
    text = SSN_RE.sub("[REDACTED_SSN]", text)
    text = CC_RE.sub("[REDACTED_CC]", text)
    text = STU_RE.sub("[REDACTED_STUDENT_ID]", text)
    text = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    return text

def sanitize_with_slm(text: str, slm_call: Optional[callable] = None) -> str:
    """Placeholder for SLM fallback or additional contextual scrubbing.
    slm_call: callable that accepts and returns text (e.g., a local SLM wrapper)
    """
    deterministic = redact(text)
    if slm_call is None:
        return deterministic
    try:
        # pass deterministic-first result to SLM for contextual checks
        return slm_call(deterministic)
    except Exception:
        return deterministic
