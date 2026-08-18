import sys
import os
# Ensure project root is on sys.path so package imports work when running the script directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.agents import privacy_agent

FAILED = []


def expect(cond, msg):
    if not cond:
        FAILED.append(msg)


def test_luhn_redacts_real_credit_card():
    text = "Customer card: 4111 1111 1111 1111"
    out = privacy_agent.redact(text)
    expect("[REDACTED_CC]" in out, "Real CC should be redacted")


def test_non_luhn_numeric_not_redacted():
    text = "Order number: 1234 5678 9012 345"
    out = privacy_agent.redact(text)
    expect("[REDACTED_CC]" not in out, "Non-Luhn numeric should not be redacted")
    expect("Order number" in out, "Original text should remain")


def test_email_redaction_valid_and_invalid():
    # Use a non-reserved domain that email-validator accepts
    text = "Send to user@iana.org and leave not-an-email@com.plain"
    out = privacy_agent.redact(text)
    expect("[REDACTED_EMAIL]" in out, "Valid email should be redacted")
    expect("not-an-email@com.plain" in out, "Invalid email candidate should remain")


def test_sanitize_with_slm_fallback_on_exception():
    def broken_slm(s: str) -> str:
        raise RuntimeError("SLM failure")

    text = "Contact: user@iana.org"
    out = privacy_agent.sanitize_with_slm(text, slm_call=broken_slm)
    expect("[REDACTED_EMAIL]" in out, "Deterministic redaction returned on SLM failure")


if __name__ == '__main__':
    tests = [
        test_luhn_redacts_real_credit_card,
        test_non_luhn_numeric_not_redacted,
        test_email_redaction_valid_and_invalid,
        test_sanitize_with_slm_fallback_on_exception,
    ]
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
        except Exception as e:
            print(f"ERROR running {t.__name__}: {e}")
            FAILED.append(f"Exception in {t.__name__}: {e}")

    if FAILED:
        print("\nFailures:\n- " + "\n- ".join(FAILED))
        sys.exit(1)
    else:
        print("\nAll tests passed")
        sys.exit(0)
