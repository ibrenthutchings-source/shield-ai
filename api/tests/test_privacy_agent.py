from app.agents.privacy_agent import PrivacySanitizerAgent


def test_redacts_ssn():
    agent = PrivacySanitizerAgent()
    result = agent.sanitize("Student SSN is 123-45-6789 on file.")

    assert "123-45-6789" not in result.redacted
    assert "[REDACTED_SSN]" in result.redacted
    assert result.redaction_counts["ssn"] == 1


def test_redacts_student_id():
    agent = PrivacySanitizerAgent()
    result = agent.sanitize("Please look up record STU-482913 for the transcript.")

    assert "STU-482913" not in result.redacted
    assert "[REDACTED_STUDENT_ID]" in result.redacted
    assert result.redaction_counts["student_id"] == 1


def test_redacts_credit_card_with_dashes():
    agent = PrivacySanitizerAgent()
    result = agent.sanitize("Card on file: 4111-1111-1111-1111 for the donation.")

    assert "4111-1111-1111-1111" not in result.redacted
    assert "[REDACTED_CREDIT_CARD]" in result.redacted
    assert result.redaction_counts["credit_card"] == 1


def test_redacts_personal_email():
    agent = PrivacySanitizerAgent()
    result = agent.sanitize("Contact parent at jane.doe@example.com about the incident.")

    assert "jane.doe@example.com" not in result.redacted
    assert "[REDACTED_EMAIL]" in result.redacted
    assert result.redaction_counts["email"] == 1


def test_redacts_multiple_identifiers_in_one_pass():
    agent = PrivacySanitizerAgent()
    text = "SSN 123-45-6789, student STU-100200, contact bob@school.org"
    result = agent.sanitize(text)

    assert result.redaction_counts == {"ssn": 1, "student_id": 1, "email": 1}


def test_no_matches_leaves_text_unchanged_and_counts_empty():
    agent = PrivacySanitizerAgent()
    result = agent.sanitize("No sensitive data in this ticket.")

    assert result.redacted == "No sensitive data in this ticket."
    assert result.redaction_counts == {}


def test_slm_fallback_runs_on_already_redacted_text():
    calls: list[str] = []

    def fake_slm(text: str) -> str:
        calls.append(text)
        return text.replace("Bob Smith", "[REDACTED_NAME]")

    agent = PrivacySanitizerAgent(slm_fallback=fake_slm)
    result = agent.sanitize("Bob Smith's SSN is 123-45-6789.")

    assert calls == ["Bob Smith's SSN is [REDACTED_SSN]."]
    assert result.redacted == "[REDACTED_NAME]'s SSN is [REDACTED_SSN]."


def test_original_text_is_preserved_unmodified():
    agent = PrivacySanitizerAgent()
    original = "SSN 123-45-6789"
    result = agent.sanitize(original)

    assert result.original == original


def test_non_luhn_digit_run_is_not_redacted_as_credit_card():
    agent = PrivacySanitizerAgent()
    # 16 digits but fails the Luhn checksum -> not a real card number.
    result = agent.sanitize("Tracking number: 1234567890123456")

    assert "1234567890123456" in result.redacted
    assert "credit_card" not in result.redaction_counts


def test_malformed_email_candidate_is_not_redacted():
    agent = PrivacySanitizerAgent()
    # Consecutive dots in the local part make this syntactically invalid.
    result = agent.sanitize("Ref code: a..b@example.com")

    assert "a..b@example.com" in result.redacted
    assert "email" not in result.redaction_counts


def test_slm_fallback_exception_falls_back_to_deterministic_redaction():
    def broken_slm(text: str) -> str:
        raise RuntimeError("local model unavailable")

    agent = PrivacySanitizerAgent(slm_fallback=broken_slm)
    result = agent.sanitize("SSN is 123-45-6789.")

    assert result.redacted == "SSN is [REDACTED_SSN]."
    assert result.redaction_counts == {"ssn": 1}
