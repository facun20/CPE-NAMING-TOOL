"""
UI components and utilities for the UBC CPE File Naming Tool.

Includes template management, usage analytics tracking, accessibility
helpers, and shared CSS/styling.
"""

import json
import csv
import io
from datetime import datetime


# ─── Custom CSS ────────────────────────────────────────────────────────────

CUSTOM_CSS = """
<style>
    :root {
        --ubc-blue: #002145;
        --ubc-gold: #C1A01E;
        --ubc-light-bg: #f8f9fa;
    }

    /* Main header */
    .main-header {
        text-align: center;
        padding: 20px;
        border-bottom: 3px solid #002145;
        margin-bottom: 20px;
    }

    .main-header h1 {
        color: #002145;
        margin-bottom: 5px;
    }

    .version-badge {
        background-color: #C1A01E;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: 600;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background-color: #e8e8e8;
        border-radius: 8px;
        padding: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 6px;
        padding: 10px 24px;
        font-weight: 500;
        color: #333;
    }

    .stTabs [aria-selected="true"] {
        background-color: #002145 !important;
        color: white !important;
        font-weight: 600;
        border-radius: 6px;
    }

    /* Output box */
    .output-box {
        background-color: #f8f8f8;
        border-left: 4px solid #C1A01E;
        padding: 15px;
        border-radius: 0 8px 8px 0;
        margin: 10px 0;
    }

    /* File suggestion card */
    .file-suggestion {
        background-color: #f8fbff;
        border: 1px solid #d0dae8;
        border-left: 4px solid #002145;
        border-radius: 0 8px 8px 0;
        padding: 15px 20px;
        margin: 10px 0;
    }

    /* Help panel */
    .help-panel {
        background-color: #f8f8f8;
        border-left: 4px solid #C1A01E;
        padding: 15px;
        border-radius: 0 8px 8px 0;
    }

    /* Location result */
    .location-result {
        background-color: #e8f4e8;
        border: 2px solid #002145;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
    }

    .location-path {
        font-family: monospace;
        background-color: #f0f0f0;
        padding: 10px 15px;
        border-radius: 4px;
        font-size: 14px;
        word-wrap: break-word;
    }

    .breadcrumb {
        color: #002145;
        font-weight: 500;
    }

    .breadcrumb-separator {
        color: #C1A01E;
        margin: 0 8px;
    }

    /* PII warning banner */
    .pii-warning {
        background-color: #fff8e1;
        border: 1px solid #ffe082;
        border-left: 4px solid #ff9800;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 10px 0;
    }

    .pii-warning h4 {
        color: #e65100;
        margin: 0 0 6px 0;
        font-size: 14px;
    }

    .pii-warning .pii-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 8px 0;
    }

    .pii-tag {
        background-color: #fff3e0;
        border: 1px solid #ffcc80;
        color: #e65100;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }

    .pii-warning .pii-note {
        color: #666;
        font-size: 12px;
        margin: 6px 0 0 0;
    }

    /* PII protection badge */
    .pii-badge {
        background-color: #e8f5e9;
        border: 1px solid #a5d6a7;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 10px 0;
    }

    .pii-badge h4 {
        color: #2e7d32;
        margin: 0 0 4px 0;
        font-size: 14px;
    }

    .pii-badge p {
        color: #555;
        font-size: 12px;
        margin: 0;
        line-height: 1.4;
    }

    /* Provider info box */
    .provider-info {
        background-color: #e8f5e9;
        border: 1px solid #c8e6c9;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 10px 0;
        font-size: 13px;
    }

    /* File list item */
    .file-item {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 10px 14px;
        margin: 6px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .file-item-name {
        font-weight: 500;
        color: #333;
    }

    .file-item-status {
        font-size: 12px;
        color: #888;
    }

    /* Confidence levels */
    .confidence-high {
        color: #28a745;
        font-weight: 600;
    }

    .confidence-medium {
        color: #ffc107;
        font-weight: 600;
    }

    .confidence-low {
        color: #dc3545;
        font-weight: 600;
    }

    /* How it works list */
    .how-it-works {
        font-size: 13px;
        color: #555;
    }

    .how-it-works ol {
        padding-left: 20px;
        margin: 8px 0;
    }

    .how-it-works li {
        margin: 4px 0;
    }

    /* Accessibility: focus indicators */
    *:focus-visible {
        outline: 3px solid #C1A01E !important;
        outline-offset: 2px;
    }

    /* Reduce Streamlit default padding */
    .block-container {
        padding-bottom: 1rem !important;
    }

    footer {
        visibility: hidden;
    }
</style>
"""

ACCESSIBILITY_HTML = ""


# ─── Template Management ──────────────────────────────────────────────────


def get_default_templates() -> dict:
    """Return built-in template presets."""
    return {
        "FCCS Course Outline": {
            "format_type": "course",
            "faculty_school": "FCCS",
            "document_form": "GUI",
            "revision": "0",
            "extension": "pdf",
        },
        "FHSD-SoN Course Budget": {
            "format_type": "course",
            "faculty_school": "FHSD-SoN",
            "document_form": "BGT",
            "revision": "A",
            "extension": "xlsx",
        },
        "CPE Internal Policy": {
            "format_type": "advanced",
            "project_code": "CPE",
            "document_form": "POL",
            "revision": "0",
            "extension": "pdf",
        },
        "Meeting Minutes": {
            "format_type": "basic",
            "document_form": "MIN",
            "revision": "0",
            "extension": "docx",
        },
        "Instructor Contract": {
            "format_type": "course",
            "document_form": "CON",
            "revision": "0",
            "extension": "pdf",
        },
        "Marketing Presentation": {
            "format_type": "advanced",
            "project_code": "CPE",
            "document_form": "PRS",
            "revision": "A",
            "extension": "pptx",
        },
    }


def save_custom_template(st_session, name: str, template_data: dict):
    """Save a custom template to session state."""
    if "custom_templates" not in st_session:
        st_session["custom_templates"] = {}
    st_session["custom_templates"][name] = template_data


def get_all_templates(st_session) -> dict:
    """Get all templates (defaults + custom)."""
    templates = get_default_templates()
    if "custom_templates" in st_session:
        templates.update(st_session["custom_templates"])
    return templates


def delete_custom_template(st_session, name: str):
    """Delete a custom template from session state."""
    if "custom_templates" in st_session and name in st_session["custom_templates"]:
        del st_session["custom_templates"][name]


# ─── Usage Analytics ───────────────────────────────────────────────────────


def init_analytics(st_session):
    """Initialize analytics tracking in session state."""
    if "analytics" not in st_session:
        st_session["analytics"] = {
            "formats_used": {"basic": 0, "advanced": 0, "course": 0},
            "partners_used": {},
            "document_forms_used": {},
            "ai_provider_used": {"gemini": 0, "claude": 0, "offline": 0},
            "files_analyzed": 0,
            "filenames_generated": 0,
            "locations_generated": 0,
            "session_start": datetime.now().isoformat(),
        }


def track_filename_generated(st_session, format_type: str, document_form: str = "", partner: str = ""):
    """Track a filename generation event."""
    init_analytics(st_session)
    analytics = st_session["analytics"]
    analytics["filenames_generated"] += 1
    analytics["formats_used"][format_type] = analytics["formats_used"].get(format_type, 0) + 1
    if document_form:
        analytics["document_forms_used"][document_form] = (
            analytics["document_forms_used"].get(document_form, 0) + 1
        )
    if partner:
        analytics["partners_used"][partner] = analytics["partners_used"].get(partner, 0) + 1


def track_ai_analysis(st_session, provider: str, file_count: int = 1):
    """Track an AI analysis event."""
    init_analytics(st_session)
    analytics = st_session["analytics"]
    analytics["files_analyzed"] += file_count
    analytics["ai_provider_used"][provider] = (
        analytics["ai_provider_used"].get(provider, 0) + file_count
    )


def track_location_generated(st_session):
    """Track a location generation event."""
    init_analytics(st_session)
    st_session["analytics"]["locations_generated"] += 1


def get_analytics_summary(st_session) -> dict:
    """Get analytics summary for display."""
    init_analytics(st_session)
    return st_session["analytics"]


# ─── Batch Export ──────────────────────────────────────────────────────────


def export_results_to_csv(results: list) -> str:
    """Export AI analysis results to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Original Filename",
        "Suggested Filename",
        "Format Used",
        "Faculty-School",
        "Course Code",
        "Term",
        "Project Code",
        "Subject",
        "Document Form",
        "Date",
        "Revision",
        "Confidence",
        "AI Reasoning",
    ])

    for result in results:
        if result.get("success"):
            analysis = result["analysis"]
            extracted = analysis.get("extractedFields", {})
            writer.writerow([
                result.get("file", ""),
                analysis.get("suggestedName", ""),
                analysis.get("formatUsed", ""),
                extracted.get("facultySchool", ""),
                extracted.get("courseCode", ""),
                extracted.get("term", ""),
                extracted.get("projectCode", ""),
                extracted.get("subject", ""),
                extracted.get("documentForm", ""),
                extracted.get("date", ""),
                extracted.get("revision", ""),
                analysis.get("confidence", ""),
                analysis.get("reasoning", ""),
            ])
        else:
            writer.writerow([
                result.get("file", ""),
                "ERROR",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                result.get("error", "Unknown error"),
            ])

    return output.getvalue()


# ─── Result Persistence ───────────────────────────────────────────────────


def save_results(st_session, results: list):
    """Save analysis results to session state for persistence."""
    if "saved_results" not in st_session:
        st_session["saved_results"] = []
    timestamp = datetime.now().isoformat()
    for result in results:
        result["timestamp"] = timestamp
    st_session["saved_results"].extend(results)


def get_saved_results(st_session) -> list:
    """Get previously saved results."""
    return st_session.get("saved_results", [])


def clear_saved_results(st_session):
    """Clear saved results."""
    st_session["saved_results"] = []
