"""Tests for filename_generator module."""

import pytest
from datetime import datetime, date

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from filename_generator import (
    generate_filename,
    validate_subject,
    validate_course_code,
    validate_term,
    validate_project_code,
    validate_faculty_school,
    validate_all_fields,
    check_filename_length,
)


class TestGenerateFilename:
    def test_basic_format(self):
        standard, sharepoint = generate_filename(
            "basic", "NamingConventions", date(2025, 3, 15), "0", "pdf"
        )
        assert standard == "NamingConventions_2025-03-15_Rev0.pdf"
        assert sharepoint == "NamingConventions 2025-03-15 Rev0.pdf"

    def test_advanced_format_with_project_and_doc_form(self):
        standard, _ = generate_filename(
            "advanced", "RecordsManagement", date(2025, 1, 20), "A", "docx",
            project_code="CPE", document_form="POL",
        )
        assert standard == "CPE_RecordsManagement_POL_2025-01-20_RevA.docx"

    def test_advanced_format_without_project(self):
        standard, _ = generate_filename(
            "advanced", "TestSubject", date(2025, 6, 1), "B", "xlsx",
            document_form="RPT",
        )
        assert standard == "TestSubject_RPT_2025-06-01_RevB.xlsx"

    def test_course_format_full(self):
        standard, _ = generate_filename(
            "course", "CourseOutline", date(2025, 1, 10), "0", "pptx",
            faculty_school="FHSD-SoN", course_code="0386-0001",
            term="2024WT2", document_form="TEM",
        )
        assert standard == "FHSD-SoN_0386-0001_2024WT2_CourseOutline_TEM_2025-01-10_Rev0.pptx"

    def test_course_format_partial(self):
        standard, _ = generate_filename(
            "course", "Syllabus", date(2025, 5, 1), "0", "pdf",
            faculty_school="FCCS",
        )
        assert standard == "FCCS_Syllabus_2025-05-01_Rev0.pdf"

    def test_sharepoint_uses_spaces(self):
        _, sharepoint = generate_filename(
            "basic", "Test", date(2025, 1, 1), "0", "pdf"
        )
        assert "_" not in sharepoint.replace("Rev0", "")  # No underscores except in Rev0

    def test_draft_revision(self):
        standard, _ = generate_filename(
            "basic", "Draft", date(2025, 1, 1), "0A", "pdf"
        )
        assert "Rev0A" in standard


class TestValidateSubject:
    def test_empty_subject(self):
        result = validate_subject("")
        assert not result.valid

    def test_valid_subject(self):
        result = validate_subject("NamingConventions")
        assert result.valid

    def test_subject_with_spaces(self):
        result = validate_subject("Naming Conventions")
        assert not result.valid

    def test_subject_too_long(self):
        result = validate_subject("A" * 51)
        assert not result.valid

    def test_subject_with_hyphens(self):
        result = validate_subject("Naming-Conventions")
        assert result.valid

    def test_subject_special_chars(self):
        result = validate_subject("Name@#$%")
        assert not result.valid


class TestValidateCourseCode:
    def test_empty_is_valid(self):
        assert validate_course_code("").valid

    def test_valid_format(self):
        assert validate_course_code("0386-0001").valid

    def test_invalid_format_no_dash(self):
        assert not validate_course_code("03860001").valid

    def test_invalid_format_wrong_digits(self):
        assert not validate_course_code("038-0001").valid

    def test_invalid_format_letters(self):
        assert not validate_course_code("ABCD-0001").valid


class TestValidateTerm:
    def test_empty_is_valid(self):
        assert validate_term("").valid

    def test_valid_winter_term(self):
        assert validate_term("2024WT1").valid

    def test_valid_summer_term(self):
        assert validate_term("2025ST2").valid

    def test_invalid_session(self):
        assert not validate_term("2024AT1").valid

    def test_invalid_term_number(self):
        assert not validate_term("2024WT3").valid

    def test_invalid_year(self):
        assert not validate_term("1999WT1").valid


class TestValidateProjectCode:
    def test_empty_is_valid(self):
        assert validate_project_code("").valid

    def test_valid_code(self):
        assert validate_project_code("CPE").valid

    def test_valid_code_with_numbers(self):
        assert validate_project_code("PROJ2024").valid

    def test_too_long(self):
        assert not validate_project_code("A" * 21).valid

    def test_special_chars(self):
        assert not validate_project_code("CPE@123").valid


class TestValidateAllFields:
    def test_basic_valid(self):
        errors = validate_all_fields("basic", "ValidSubject")
        assert len(errors) == 0

    def test_basic_missing_subject(self):
        errors = validate_all_fields("basic", "")
        assert len(errors) > 0

    def test_course_format_validates_all(self):
        errors = validate_all_fields(
            "course", "Subject", course_code="bad-format", term="invalid"
        )
        assert len(errors) >= 2


class TestCheckFilenameLength:
    def test_short_filename(self):
        result = check_filename_length("short.pdf")
        assert result.valid
        assert result.level == "info"

    def test_warning_length(self):
        result = check_filename_length("x" * 110 + ".pdf")
        assert result.valid
        assert result.level == "warning"

    def test_error_length(self):
        result = check_filename_length("x" * 160 + ".pdf")
        assert not result.valid
        assert result.level == "error"
