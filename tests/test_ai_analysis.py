"""Tests for ai_analysis module."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ai_analysis import (
    analyze_with_rules,
    get_confidence_level,
    _parse_ai_response,
    _build_analysis_prompt,
)


class TestRuleBasedAnalysis:
    def test_basic_text_analysis(self):
        result = analyze_with_rules(
            "This is a report about enrollment counts",
            "enrollment_report.pdf",
            "text",
        )
        assert result["success"]
        analysis = result["analysis"]
        assert analysis["suggestedName"].endswith(".pdf")
        assert analysis["confidence"] <= 5  # Rule-based should have low confidence

    def test_detects_document_form(self):
        result = analyze_with_rules(
            "Meeting minutes from the staff meeting held on January 15",
            "meeting_notes.docx",
            "text",
        )
        assert result["success"]
        extracted = result["analysis"]["extractedFields"]
        assert extracted["documentForm"] == "MIN"

    def test_detects_faculty(self):
        result = analyze_with_rules(
            "Faculty of Creative and Critical Studies program review",
            "program_review.pdf",
            "text",
        )
        assert result["success"]
        extracted = result["analysis"]["extractedFields"]
        assert extracted["facultySchool"] == "FCCS"

    def test_detects_course_code(self):
        result = analyze_with_rules(
            "Course 0386-0001 Winter 2024",
            "course_info.pdf",
            "text",
        )
        assert result["success"]
        extracted = result["analysis"]["extractedFields"]
        assert extracted["courseCode"] == "0386-0001"

    def test_detects_term(self):
        result = analyze_with_rules(
            "Term: 2024WT1 section overview",
            "section.pdf",
            "text",
        )
        assert result["success"]
        extracted = result["analysis"]["extractedFields"]
        assert extracted["term"] == "2024WT1"

    def test_image_content_type(self):
        result = analyze_with_rules(
            "data:image/png;base64,abc123",
            "photo.png",
            "image",
        )
        assert result["success"]
        assert result["analysis"]["suggestedName"].endswith(".png")

    def test_subject_from_filename(self):
        result = analyze_with_rules("Some content", "my_document.pdf", "text")
        assert result["success"]
        subject = result["analysis"]["extractedFields"]["subject"]
        assert subject  # Should derive something from filename

    def test_date_extraction_iso(self):
        result = analyze_with_rules(
            "Document dated 2025-06-15 for review",
            "test.pdf",
            "text",
        )
        assert result["success"]
        extracted = result["analysis"]["extractedFields"]
        assert extracted["date"] == "2025-06-15"

    def test_course_format_used_when_faculty_and_course(self):
        result = analyze_with_rules(
            "Faculty of Creative and Critical Studies course 0386-0001",
            "test.pdf",
            "text",
        )
        assert result["success"]
        assert result["analysis"]["formatUsed"] == "course"


class TestConfidenceLevel:
    def test_high_confidence(self):
        info = get_confidence_level(9)
        assert info["level"] == "high"
        assert info["color"] == "green"

    def test_medium_confidence(self):
        info = get_confidence_level(6)
        assert info["level"] == "medium"
        assert info["color"] == "orange"

    def test_low_confidence(self):
        info = get_confidence_level(3)
        assert info["level"] == "low"
        assert info["color"] == "red"

    def test_boundary_high(self):
        assert get_confidence_level(8)["level"] == "high"

    def test_boundary_medium(self):
        assert get_confidence_level(5)["level"] == "medium"

    def test_boundary_low(self):
        assert get_confidence_level(4)["level"] == "low"


class TestParseAIResponse:
    def test_valid_json(self):
        response = '{"suggestedName": "Test_Rev0.pdf", "confidence": 8}'
        result = _parse_ai_response(response, "test.pdf", "2025-01-01")
        assert result["success"]
        assert result["analysis"]["suggestedName"] == "Test_Rev0.pdf"

    def test_json_in_markdown(self):
        response = '```json\n{"suggestedName": "Test_Rev0.pdf"}\n```'
        result = _parse_ai_response(response, "test.pdf", "2025-01-01")
        assert result["success"]

    def test_invalid_json_fallback(self):
        response = "This is not JSON at all"
        result = _parse_ai_response(response, "test.pdf", "2025-01-01")
        assert result["success"]
        assert result["analysis"]["confidence"] == 3  # Low confidence fallback

    def test_fallback_preserves_extension(self):
        result = _parse_ai_response("bad response", "report.xlsx", "2025-01-01")
        assert result["analysis"]["suggestedName"].endswith(".xlsx")


class TestBuildAnalysisPrompt:
    def test_text_prompt_contains_file_name(self):
        prompt = _build_analysis_prompt("test.pdf", "2025-01-01", "text")
        assert "test.pdf" in prompt
        assert "2025-01-01" in prompt

    def test_image_pdf_prompt(self):
        prompt = _build_analysis_prompt("doc.pdf", "2025-01-01", "image", is_pdf=True)
        assert "PDF" in prompt
        assert "FACULTY-SCHOOL" in prompt

    def test_image_photo_prompt(self):
        prompt = _build_analysis_prompt("photo.jpg", "2025-01-01", "image", is_pdf=False)
        assert "IMG" in prompt or "SCR" in prompt
