"""Tests for ui_components module."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ui_components import (
    get_default_templates,
    get_all_templates,
    save_custom_template,
    delete_custom_template,
    init_analytics,
    track_filename_generated,
    track_ai_analysis,
    track_location_generated,
    get_analytics_summary,
    export_results_to_csv,
    save_results,
    get_saved_results,
    clear_saved_results,
    CUSTOM_CSS,
)


class MockSessionState(dict):
    """Mock for st.session_state."""
    pass


class TestTemplates:
    def test_default_templates_exist(self):
        templates = get_default_templates()
        assert len(templates) > 0
        assert "Meeting Minutes" in templates

    def test_default_template_structure(self):
        templates = get_default_templates()
        for name, tmpl in templates.items():
            assert "format_type" in tmpl
            assert tmpl["format_type"] in ("basic", "advanced", "course")

    def test_save_custom_template(self):
        session = MockSessionState()
        save_custom_template(session, "My Template", {"format_type": "basic"})
        assert "My Template" in session["custom_templates"]

    def test_get_all_templates_merges(self):
        session = MockSessionState()
        save_custom_template(session, "Custom", {"format_type": "course"})
        all_templates = get_all_templates(session)
        assert "Custom" in all_templates
        assert "Meeting Minutes" in all_templates  # Default still present

    def test_delete_custom_template(self):
        session = MockSessionState()
        save_custom_template(session, "ToDelete", {"format_type": "basic"})
        delete_custom_template(session, "ToDelete")
        assert "ToDelete" not in session.get("custom_templates", {})


class TestAnalytics:
    def test_init_analytics(self):
        session = MockSessionState()
        init_analytics(session)
        assert "analytics" in session
        assert "formats_used" in session["analytics"]

    def test_track_filename(self):
        session = MockSessionState()
        init_analytics(session)
        track_filename_generated(session, "basic", "RPT", "FCCS")
        assert session["analytics"]["filenames_generated"] == 1
        assert session["analytics"]["formats_used"]["basic"] == 1
        assert session["analytics"]["document_forms_used"]["RPT"] == 1

    def test_track_ai_analysis(self):
        session = MockSessionState()
        init_analytics(session)
        track_ai_analysis(session, "gemini", 3)
        assert session["analytics"]["files_analyzed"] == 3
        assert session["analytics"]["ai_provider_used"]["gemini"] == 3

    def test_track_location(self):
        session = MockSessionState()
        init_analytics(session)
        track_location_generated(session)
        assert session["analytics"]["locations_generated"] == 1

    def test_analytics_summary(self):
        session = MockSessionState()
        summary = get_analytics_summary(session)
        assert "filenames_generated" in summary


class TestExport:
    def test_export_csv_with_results(self):
        results = [
            {
                "success": True,
                "file": "test.pdf",
                "analysis": {
                    "suggestedName": "Test_Rev0.pdf",
                    "formatUsed": "basic",
                    "extractedFields": {"subject": "Test", "date": "2025-01-01"},
                    "confidence": 8,
                    "reasoning": "Test reasoning",
                },
            }
        ]
        csv_data = export_results_to_csv(results)
        assert "test.pdf" in csv_data
        assert "Test_Rev0.pdf" in csv_data

    def test_export_csv_with_error(self):
        results = [
            {"success": False, "file": "bad.pdf", "error": "API error"}
        ]
        csv_data = export_results_to_csv(results)
        assert "ERROR" in csv_data
        assert "API error" in csv_data

    def test_export_csv_empty(self):
        csv_data = export_results_to_csv([])
        assert "Original Filename" in csv_data  # Header still present


class TestResultPersistence:
    def test_save_and_get_results(self):
        session = MockSessionState()
        results = [{"success": True, "file": "test.pdf", "analysis": {}}]
        save_results(session, results)
        saved = get_saved_results(session)
        assert len(saved) == 1

    def test_clear_results(self):
        session = MockSessionState()
        save_results(session, [{"file": "test.pdf"}])
        clear_saved_results(session)
        assert len(get_saved_results(session)) == 0

    def test_multiple_saves_accumulate(self):
        session = MockSessionState()
        save_results(session, [{"file": "a.pdf"}])
        save_results(session, [{"file": "b.pdf"}])
        assert len(get_saved_results(session)) == 2


class TestCSS:
    def test_css_contains_ubc_colors(self):
        assert "#002145" in CUSTOM_CSS
        assert "#C1A01E" in CUSTOM_CSS

    def test_css_contains_accessibility(self):
        assert "focus-visible" in CUSTOM_CSS
        assert "skip-link" in CUSTOM_CSS
