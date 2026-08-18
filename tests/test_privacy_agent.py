import pytest
from app.agents import privacy_agent


def test_luhn_redacts_real_credit_card():
    # A commonly used test Visa number that passes Luhn
    text = "Customer card: 4111 1111 1111 1111"
    out = privacy_agent.redact(text)
    assert "[REDACTED_CC]" in out


def test_non_luhn_numeric_not_redacted():
    text = "Order number: 1234 5678 9012 345"
    out = privacy_agent.redact(text)
    # This numeric sequence should not be redacted as a CC
    assert "[REDACTED_CC]" not in out
    assert "Order number" in out


def test_email_redaction_valid_and_invalid():
    # Use a non-reserved domain that email-validator accepts
    text = "Send to user@iana.org and leave not-an-email@com.plain"
    out = privacy_agent.redact(text)
    assert "[REDACTED_EMAIL]" in out
    # invalid candidate should remain
    assert "not-an-email@com.plain" in out


def test_sanitize_with_slm_fallback_on_exception():
    def broken_slm(s: str) -> str:
        raise RuntimeError("SLM failure")

    text = "Contact: user@iana.org"
    out = privacy_agent.sanitize_with_slm(text, slm_call=broken_slm)
    # On SLM failure, the deterministic redaction is returned
    assert "[REDACTED_EMAIL]" in out
