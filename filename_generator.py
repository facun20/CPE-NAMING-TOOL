"""
Filename generation and validation for the UBC CPE File Naming Tool.

Handles generating CPE-compliant filenames in basic, advanced, and course
formats, plus input validation for all filename components.
"""

import re
from datetime import datetime

from constants import (
    DOCUMENT_FORMS,
    REVISION_STATUSES,
    FILE_EXTENSIONS,
    PARTNERS,
    MAX_SUBJECT_LENGTH,
    FILENAME_WARN_LENGTH,
    FILENAME_ERROR_LENGTH,
)


class ValidationResult:
    """Result of a validation check."""

    def __init__(self, valid: bool, message: str = "", level: str = "error"):
        self.valid = valid
        self.message = message
        self.level = level  # "error", "warning", "info"


def validate_subject(subject: str) -> ValidationResult:
    """Validate and check the subject field."""
    if not subject:
        return ValidationResult(False, "Subject is required.")
    if len(subject) > MAX_SUBJECT_LENGTH:
        return ValidationResult(
            False,
            f"Subject exceeds {MAX_SUBJECT_LENGTH} characters ({len(subject)}). Please shorten.",
            "warning",
        )
    if " " in subject:
        return ValidationResult(
            False,
            "Subject should not contain spaces. Use PascalCase (e.g., NamingConventions).",
        )
    if not re.match(r"^[A-Za-z0-9\-]+$", subject):
        return ValidationResult(
            False,
            "Subject should only contain letters, numbers, and hyphens.",
        )
    return ValidationResult(True)


def validate_course_code(course_code: str) -> ValidationResult:
    """Validate course code format (####-####)."""
    if not course_code:
        return ValidationResult(True)  # Optional
    if not re.match(r"^\d{4}-\d{4}$", course_code):
        return ValidationResult(
            False,
            "Course code must be in format ####-#### (e.g., 0386-0001).",
        )
    return ValidationResult(True)


def validate_term(term: str) -> ValidationResult:
    """Validate term format (YYYYST)."""
    if not term:
        return ValidationResult(True)  # Optional
    if not re.match(r"^\d{4}[WS]T[12]$", term):
        return ValidationResult(
            False,
            "Term must be in format YYYYST (e.g., 2024WT1, 2025ST2).",
        )
    year = int(term[:4])
    if year < 2000 or year > 2050:
        return ValidationResult(False, "Year must be between 2000 and 2050.")
    return ValidationResult(True)


def validate_project_code(project_code: str) -> ValidationResult:
    """Validate project/account code."""
    if not project_code:
        return ValidationResult(True)  # Optional
    if not re.match(r"^[A-Za-z0-9\-]+$", project_code):
        return ValidationResult(
            False,
            "Project code should only contain letters, numbers, and hyphens.",
        )
    if len(project_code) > 20:
        return ValidationResult(False, "Project code should be 20 characters or less.")
    return ValidationResult(True)


def validate_faculty_school(faculty_school: str) -> ValidationResult:
    """Validate faculty-school code."""
    if not faculty_school:
        return ValidationResult(True)  # Optional
    valid_codes = [k for k in PARTNERS.keys() if k]
    if faculty_school not in valid_codes:
        return ValidationResult(
            True,
            f"'{faculty_school}' is not a recognized partner code. Known codes: {', '.join(valid_codes)}",
            "warning",
        )
    return ValidationResult(True)


def validate_all_fields(
    format_type: str,
    subject: str,
    project_code: str = "",
    document_form: str = "",
    faculty_school: str = "",
    course_code: str = "",
    term: str = "",
) -> list[ValidationResult]:
    """Run all validations and return list of results."""
    results = []

    results.append(validate_subject(subject))

    if format_type in ("advanced", "course"):
        results.append(validate_project_code(project_code))

    if format_type == "course":
        results.append(validate_faculty_school(faculty_school))
        results.append(validate_course_code(course_code))
        results.append(validate_term(term))

    return [r for r in results if not r.valid]


def generate_filename(
    format_type: str,
    subject: str,
    date_val: datetime,
    revision: str,
    extension: str,
    project_code: str = "",
    document_form: str = "",
    faculty_school: str = "",
    course_code: str = "",
    term: str = "",
) -> tuple:
    """Generate CPE-compliant filename. Returns (standard_filename, sharepoint_filename)."""
    formatted_date = date_val.strftime("%Y-%m-%d")
    elements = []

    if format_type == "basic":
        elements = [subject, formatted_date, f"Rev{revision}"]
    elif format_type == "advanced":
        if project_code:
            elements.append(project_code)
        elements.append(subject)
        if document_form:
            elements.append(document_form)
        elements.append(formatted_date)
        elements.append(f"Rev{revision}")
    elif format_type == "course":
        if faculty_school:
            elements.append(faculty_school)
        if course_code:
            elements.append(course_code)
        if term:
            elements.append(term)
        elements.append(subject)
        if document_form:
            elements.append(document_form)
        elements.append(formatted_date)
        elements.append(f"Rev{revision}")

    standard_filename = "_".join(elements) + "." + extension
    sharepoint_filename = " ".join(elements) + "." + extension

    return standard_filename, sharepoint_filename


def check_filename_length(filename: str) -> ValidationResult:
    """Check if filename length is acceptable."""
    char_count = len(filename)
    if char_count > FILENAME_ERROR_LENGTH:
        return ValidationResult(
            False,
            f"{char_count} characters - Too long! May cause system issues.",
            "error",
        )
    elif char_count > FILENAME_WARN_LENGTH:
        return ValidationResult(
            True,
            f"{char_count} characters - Consider shortening.",
            "warning",
        )
    return ValidationResult(True, f"{char_count} characters", "info")
