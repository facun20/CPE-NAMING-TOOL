"""
File location path generation for the UBC CPE File Naming Tool.

Determines the correct folder location for documents based on whether
they are partner-related or CPE internal, and navigates through the
organizational structure.
"""

from constants import (
    CPE_INTERNAL_BLOCKS,
    DEFINITION_APPROVALS_BLOCKS,
    PRODUCTION_DELIVERY_BLOCKS,
)


def generate_file_location_path(
    is_partner_related: bool,
    cpe_block: str = "",
    cpe_subcat: str = "",
    partner: str = "",
    phase: str = "",
    subject_area: str = "",
    credential: str = "",
    applies_to_all: bool = True,
    occurrence: str = "",
    file_type: str = "",
) -> tuple:
    """Generate file location path based on selections.

    Returns (breadcrumb_path, folder_path)
    """
    breadcrumb_parts = []
    folder_parts = []

    if not is_partner_related:
        # CPE Internal path
        breadcrumb_parts.append("CPE Internal")
        folder_parts.append("CPE Internal")

        if cpe_block:
            block_name = CPE_INTERNAL_BLOCKS.get(cpe_block, cpe_block)
            breadcrumb_parts.append(block_name)
            folder_parts.append(block_name)

            if cpe_subcat:
                breadcrumb_parts.append(cpe_subcat)
                folder_parts.append(cpe_subcat)
    else:
        # Partner-related path
        if partner:
            partner_name = partner
            breadcrumb_parts.append(f"Partner ({partner_name})")
            folder_parts.append(partner_name)

            if phase:
                breadcrumb_parts.append(phase)
                folder_parts.append(phase)

                if phase == "Definition and Approvals":
                    if subject_area:
                        breadcrumb_parts.append(subject_area)
                        folder_parts.append(subject_area)

                        if file_type:
                            breadcrumb_parts.append(file_type)
                            folder_parts.append(file_type)
                else:  # Production & Delivery
                    if credential:
                        breadcrumb_parts.append(credential)
                        folder_parts.append(credential)

                        if not applies_to_all and occurrence:
                            breadcrumb_parts.append(occurrence)
                            folder_parts.append(occurrence)

                        if file_type:
                            breadcrumb_parts.append(file_type)
                            folder_parts.append(file_type)

    breadcrumb_path = " \u2192 ".join(breadcrumb_parts)
    folder_path = " / ".join(folder_parts)

    return breadcrumb_path, folder_path
