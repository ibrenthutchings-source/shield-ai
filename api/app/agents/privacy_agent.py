import logging
import re
from collections.abc import Callable

from email_validator import EmailNotValidError, validate_email

from app.schemas.privacy import RedactionResult

logger = logging.getLogger(__name__)

SLMFallback = Callable[[str], str]

_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_STUDENT_ID_RE = re.compile(r"\bSTU-\d{6}\b")
_CREDIT_CARD_CANDIDATE_RE = re.compile(r"\b(?:\d[ -]?){12,15}\d\b")
_EMAIL_CANDIDATE_RE = re.compile(r"[\w.-]+@[\w.-]+\.\w+")


def _luhn_valid(candidate: str) -> bool:
    """Luhn checksum, used to cut false positives on the broad credit-card regex."""
    digits = [int(c) for c in candidate if c.isdigit()]
    if not digits:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, digit in enumerate(digits):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


class PrivacySanitizerAgent:
    """Intercepts raw logs, tickets, and user prompts before they reach a cloud LLM.

    Regex handles well-known FERPA/PCI identifiers (SSNs, credit card numbers,
    student IDs, personal emails) deterministically. Credit-card candidates
    are Luhn-checked and email candidates are validated with `email-validator`
    before redaction, since the raw regexes alone over-match plain digit runs
    and near-miss addresses. An optional SLM fallback then runs over the
    already-redacted text to catch identifiers regex can't reliably match
    (e.g. names or addresses in free text). The fallback defaults to a no-op
    passthrough so the agent works without a local model wired up; pass a
    callable (e.g. a local SLM inference call) to enable it. If the fallback
    raises, the deterministic redaction is still returned rather than leaking
    an unhandled exception.
    """

    def __init__(self, slm_fallback: SLMFallback | None = None):
        self._slm_fallback = slm_fallback or (lambda text: text)

    def sanitize(self, text: str) -> RedactionResult:
        redacted = text
        counts: dict[str, int] = {}

        redacted, count = _SSN_RE.subn("[REDACTED_SSN]", redacted)
        if count:
            counts["ssn"] = count

        redacted, count = _STUDENT_ID_RE.subn("[REDACTED_STUDENT_ID]", redacted)
        if count:
            counts["student_id"] = count

        redacted, count = self._redact_credit_cards(redacted)
        if count:
            counts["credit_card"] = count

        redacted, count = self._redact_emails(redacted)
        if count:
            counts["email"] = count

        try:
            redacted = self._slm_fallback(redacted)
        except Exception:
            logger.exception("SLM redaction fallback failed; returning deterministic redaction only")

        return RedactionResult(original=text, redacted=redacted, redaction_counts=counts)

    @staticmethod
    def _redact_credit_cards(text: str) -> tuple[str, int]:
        matched = 0

        def _replace(match: re.Match[str]) -> str:
            nonlocal matched
            if _luhn_valid(match.group(0)):
                matched += 1
                return "[REDACTED_CREDIT_CARD]"
            return match.group(0)

        return _CREDIT_CARD_CANDIDATE_RE.sub(_replace, text), matched

    @staticmethod
    def _redact_emails(text: str) -> tuple[str, int]:
        matched = 0

        def _replace(match: re.Match[str]) -> str:
            nonlocal matched
            candidate = match.group(0)
            try:
                validate_email(candidate, check_deliverability=False)
            except EmailNotValidError:
                return candidate
            matched += 1
            return "[REDACTED_EMAIL]"

        return _EMAIL_CANDIDATE_RE.sub(_replace, text), matched
