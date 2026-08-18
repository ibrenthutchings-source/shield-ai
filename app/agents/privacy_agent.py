import re
from typing import Optional, Callable
import logging

from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)

# Regex-based patterns for common sensitive data
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CC_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
STU_RE = re.compile(r"\bSTU-\d{6}\b", re.IGNORECASE)
EMAIL_CANDIDATE_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")


def _luhn_check(number_str: str) -> bool:
    """Luhn algorithm to validate candidate credit-card number strings.

    The CC_RE may match many numeric sequences; use Luhn to reduce false positives.
    """
    digits = [int(c) for c in re.sub(r"\D", "", number_str)]
    if not digits:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d = d * 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def redact(text: str) -> str:
    """Deterministic redaction pass using regexes. Returns redacted text."""

    # SSNs and student IDs are straightforward
    text = SSN_RE.sub("[REDACTED_SSN]", text)

    # For potential credit-card like tokens, validate with Luhn before redacting
    def _cc_replacer(m: re.Match) -> str:
        candidate = m.group(0)
        if _luhn_check(candidate):
            return "[REDACTED_CC]"
        # leave non-CC numeric sequences untouched to avoid over-redaction
        return candidate

    text = CC_RE.sub(_cc_replacer, text)
    text = STU_RE.sub("[REDACTED_STUDENT_ID]", text)

    # For emails, only redact candidates that validate with email-validator
    def _email_replacer(m: re.Match) -> str:
        candidate = m.group(0)
        try:
            # validate_email throws EmailNotValidError on invalid addresses
            validate_email(candidate)
            return "[REDACTED_EMAIL]"
        except EmailNotValidError:
            # If it doesn't validate, leave the text unchanged to avoid over-redaction
            return candidate

    text = EMAIL_CANDIDATE_RE.sub(_email_replacer, text)
    return text


def sanitize_with_slm(text: str, slm_call: Optional[Callable[[str], str]] = None) -> str:
    """Perform deterministic redact pass, then optionally call a contextual SLM.

    slm_call: Optional callable that accepts a string and returns a (possibly
    further-sanitized) string. If the SLM call fails, the deterministic result
    is returned and the exception is logged.
    """
    deterministic = redact(text)
    if slm_call is None:
        return deterministic
    try:
        # pass deterministic-first result to SLM for contextual checks
        return slm_call(deterministic)
    except Exception as exc:
        # Log the failure, but return the deterministic redaction to avoid leaking
        logger.exception("SLM sanitization failed; returning deterministic redaction")
        return deterministic
