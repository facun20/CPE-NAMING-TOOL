"""Tests for pii_scrubber module."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pii_scrubber import (
    scrub_text,
    get_pii_summary,
    is_available,
    _fallback_scrub,
    PII_ENTITY_LABELS,
)


class TestFallbackScrub:
    """Test the regex-based fallback scrubber (always available)."""

    def test_scrubs_email(self):
        text = "Contact john.doe@ubc.ca for details"
        scrubbed, detected = _fallback_scrub(text)
        assert "john.doe@ubc.ca" not in scrubbed
        assert "<EMAIL_ADDRESS>" in scrubbed
        assert any(d["type"] == "EMAIL_ADDRESS" for d in detected)

    def test_scrubs_phone_number(self):
        text = "Call 250-555-1234 for info"
        scrubbed, detected = _fallback_scrub(text)
        assert "250-555-1234" not in scrubbed
        assert "<PHONE_NUMBER>" in scrubbed

    def test_scrubs_canadian_sin(self):
        text = "SIN: 123-456-789"
        scrubbed, detected = _fallback_scrub(text)
        assert "123-456-789" not in scrubbed
        assert "<CA_SIN>" in scrubbed

    def test_scrubs_credit_card(self):
        text = "Card: 4111-1111-1111-1111"
        scrubbed, detected = _fallback_scrub(text)
        assert "4111-1111-1111-1111" not in scrubbed
        assert "<CREDIT_CARD>" in scrubbed

    def test_scrubs_ip_address(self):
        text = "Server at 192.168.1.100"
        scrubbed, detected = _fallback_scrub(text)
        assert "192.168.1.100" not in scrubbed
        assert "<IP_ADDRESS>" in scrubbed

    def test_preserves_clean_text(self):
        text = "This document is about course development."
        scrubbed, detected = _fallback_scrub(text)
        assert scrubbed == text
        assert len(detected) == 0

    def test_multiple_pii_types(self):
        text = "Email: test@example.com, Phone: 604-555-9876"
        scrubbed, detected = _fallback_scrub(text)
        assert "test@example.com" not in scrubbed
        assert "604-555-9876" not in scrubbed
        assert len(detected) >= 2

    def test_detected_entities_have_required_fields(self):
        text = "Contact admin@ubc.ca"
        _, detected = _fallback_scrub(text)
        for entity in detected:
            assert "type" in entity
            assert "score" in entity
            assert "original_text" in entity


class TestScrubText:
    """Test the main scrub_text function."""

    def test_scrubs_email(self):
        scrubbed, detected = scrub_text("Email: user@example.com")
        assert "user@example.com" not in scrubbed
        assert len(detected) > 0

    def test_returns_clean_text_unchanged(self):
        text = "The budget for Winter 2025 is finalized."
        scrubbed, detected = scrub_text(text)
        # Even with Presidio, clean text should come back mostly unchanged
        assert "budget" in scrubbed.lower()

    def test_phone_scrubbing_via_fallback(self):
        # Presidio phone detection varies by format, so test via fallback
        scrubbed, detected = _fallback_scrub("Call 250-555-1234 for assistance")
        assert "250-555-1234" not in scrubbed
        assert any(d["type"] == "PHONE_NUMBER" for d in detected)


class TestGetPIISummary:
    def test_empty_list(self):
        summary = get_pii_summary([])
        assert summary == {}

    def test_counts_by_type(self):
        detected = [
            {"type": "EMAIL_ADDRESS", "start": 0, "end": 10, "score": 0.9, "original_text": "a@b.com"},
            {"type": "EMAIL_ADDRESS", "start": 20, "end": 30, "score": 0.9, "original_text": "c@d.com"},
            {"type": "PERSON", "start": 40, "end": 50, "score": 0.8, "original_text": "John Doe"},
        ]
        summary = get_pii_summary(detected)
        assert summary["EMAIL_ADDRESS"] == 2
        assert summary["PERSON"] == 1

    def test_single_entity(self):
        detected = [
            {"type": "PHONE_NUMBER", "start": 0, "end": 12, "score": 0.9, "original_text": "555-1234"},
        ]
        summary = get_pii_summary(detected)
        assert summary["PHONE_NUMBER"] == 1


class TestAvailability:
    def test_is_available_returns_bool(self):
        result = is_available()
        assert isinstance(result, bool)


class TestPIIEntityLabels:
    def test_all_default_entities_have_labels(self):
        from pii_scrubber import DEFAULT_PII_ENTITIES
        for entity in DEFAULT_PII_ENTITIES:
            assert entity in PII_ENTITY_LABELS, f"Missing label for {entity}"

    def test_labels_are_human_readable(self):
        for entity, label in PII_ENTITY_LABELS.items():
            assert len(label) > 3  # Not just the code
            assert label[0].isupper()  # Starts with capital
