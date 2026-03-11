"""Tests for file_location module."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from file_location import generate_file_location_path


class TestCPEInternalPath:
    def test_basic_internal_path(self):
        breadcrumb, folder = generate_file_location_path(
            is_partner_related=False,
            cpe_block="office_management",
        )
        assert "CPE Internal" in breadcrumb
        assert "Office Management" in breadcrumb
        assert "CPE Internal" in folder

    def test_internal_with_subcategory(self):
        breadcrumb, folder = generate_file_location_path(
            is_partner_related=False,
            cpe_block="office_management",
            cpe_subcat="Staff Meetings",
        )
        assert "Staff Meetings" in breadcrumb
        assert "Staff Meetings" in folder

    def test_internal_no_block(self):
        breadcrumb, folder = generate_file_location_path(
            is_partner_related=False,
        )
        assert breadcrumb == "CPE Internal"


class TestPartnerRelatedPath:
    def test_definition_approvals_path(self):
        breadcrumb, folder = generate_file_location_path(
            is_partner_related=True,
            partner="FCCS",
            phase="Definition and Approvals",
            subject_area="Nursing Foundations",
            file_type="Market Research",
        )
        assert "FCCS" in breadcrumb
        assert "Definition and Approvals" in breadcrumb
        assert "Nursing Foundations" in breadcrumb
        assert "Market Research" in breadcrumb

    def test_production_delivery_credential_level(self):
        breadcrumb, folder = generate_file_location_path(
            is_partner_related=True,
            partner="FHSD-SoN",
            phase="Production and Delivery",
            credential="Wildland Fire Ecology",
            applies_to_all=True,
            file_type="Budget",
        )
        assert "FHSD-SoN" in breadcrumb
        assert "Production and Delivery" in breadcrumb
        assert "Wildland Fire Ecology" in breadcrumb
        assert "Budget" in breadcrumb

    def test_production_delivery_occurrence_level(self):
        breadcrumb, folder = generate_file_location_path(
            is_partner_related=True,
            partner="FCCS",
            phase="Production and Delivery",
            credential="Certificate Program",
            applies_to_all=False,
            occurrence="2025WT1",
            file_type="Instructor Contracts",
        )
        assert "2025WT1" in breadcrumb
        assert "2025WT1" in folder

    def test_no_partner_selected(self):
        breadcrumb, folder = generate_file_location_path(
            is_partner_related=True,
        )
        assert breadcrumb == ""
        assert folder == ""

    def test_arrow_separator_in_breadcrumb(self):
        breadcrumb, _ = generate_file_location_path(
            is_partner_related=False,
            cpe_block="human_resources",
        )
        assert "\u2192" in breadcrumb

    def test_slash_separator_in_folder(self):
        _, folder = generate_file_location_path(
            is_partner_related=False,
            cpe_block="human_resources",
        )
        assert "/" in folder
