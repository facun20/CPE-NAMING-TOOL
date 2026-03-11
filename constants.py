"""
Constants and data models for the UBC CPE File Naming Tool.

All document codes, partner mappings, revision statuses, help content,
and organizational structure definitions live here.
"""

# OpenRouter API configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_MODEL = "google/gemini-2.5-flash"

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Content limits
MAX_TEXT_CONTENT = 4000
MAX_EXCEL_CONTENT = 6000
MAX_EXCEL_ROWS = 100
MAX_EXCEL_COLS = 20
MAX_EXCEL_SHEETS = 3
MAX_PDF_PAGES = 10
PDF_DPI = 150
MAX_SUBJECT_LENGTH = 50
FILENAME_WARN_LENGTH = 100
FILENAME_ERROR_LENGTH = 150

# Document form codes
DOCUMENT_FORMS = {
    "": "Select document form",
    "AGD": "AGD - Agenda",
    "AGR": "AGR - Agreement",
    "ANN": "ANN - Announcement",
    "APP": "APP - Appendix",
    "ATD": "ATD - Attendance",
    "BGT": "BGT - Course Budget",
    "BRN": "BRN - Briefing Note",
    "CCP": "CCP - Concept Paper",
    "CON": "CON - Contract",
    "DAT": "DAT - Data Set",
    "FCT": "FCT - Fact Sheet",
    "FRM": "FRM - Form",
    "GRA": "GRA - Grant",
    "GUI": "GUI - Guidelines",
    "INS": "INS - Instruction",
    "INT": "INT - Interview",
    "INV": "INV - Invoice",
    "LAT": "LAT - Letter of Attendance",
    "LCO": "LCO - Letter of Completion",
    "LGL": "LGL - Legal Document",
    "LPA": "LPA - Letter of Participation",
    "LPR": "LPR - Letter of Proficiency",
    "LTR": "LTR - Letter",
    "MIN": "MIN - Minutes",
    "MNL": "MNL - Manual",
    "NCC": "NCC - Non-Credit Certificate",
    "NCM": "NCM - Non-Credit MicroCertificate",
    "PLN": "PLN - Plan",
    "POL": "POL - Policy",
    "PRC": "PRC - Procedure",
    "PRO": "PRO - Proposal",
    "PRS": "PRS - Presentation",
    "PST": "PST - Poster",
    "RPT": "RPT - Report",
    "RVW": "RVW - Review",
    "SCH": "SCH - Schedule",
    "SMP": "SMP - Sample",
    "SRY": "SRY - Survey",
    "SUM": "SUM - Summary",
    "TEM": "TEM - Template",
    "TML": "TML - Timeline",
    "IMG": "IMG - Image",
    "SCR": "SCR - Screenshot",
    "DIA": "DIA - Diagram",
}

REVISION_STATUSES = {
    "A": "A - Initial draft sent for review",
    "B": "B - Official draft sent for external or internal review",
    "C": "C - Next incarnation of official draft",
    "0": "0 - First final revision",
    "0A": "0A - Draft after final has been produced",
    "0B": "0B - Draft after final has been produced",
    "0C": "0C - Draft after final has been produced",
    "1": "1 - Next revision after final",
}

FILE_EXTENSIONS = {
    "pdf": "pdf - Portable Document Format",
    "docx": "docx - Word Document",
    "xlsx": "xlsx - Excel Spreadsheet",
    "pptx": "pptx - PowerPoint Presentation",
    "txt": "txt - Text File",
    "csv": "csv - Comma Separated Values",
    "jpg": "jpg - JPEG Image",
    "png": "png - PNG Image",
}

# Partner (Faculty-School) codes for file location
PARTNERS = {
    "": "Select a partner...",
    "IKBASS": "IKBASS - Irving K. Barber Faculty of Arts and Social Sciences",
    "IKBFOS": "IKBFOS - Irving K. Barber Faculty of Science",
    "FCCS": "FCCS - Faculty of Creative and Critical Studies",
    "OSE": "OSE - Okanagan School of Education",
    "APSC-SoE": "APSC-SoE - Faculty of Applied Science - School of Engineering",
    "FHSD-SoN": "FHSD-SoN - Faculty of Health and Social Development - School of Nursing",
    "FHSD-SSW": "FHSD-SSW - Faculty of Health and Social Development - School of Social Work",
    "FHSD-SHES": "FHSD-SHES - Faculty of Health and Social Development - School of Health and Exercise Sciences",
    "FoM": "FoM - Faculty of Management",
    "MED": "MED - Faculty of Medicine",
    "CoGS": "CoGS - College of Graduate Studies",
}

# CPE Internal functional blocks
CPE_INTERNAL_BLOCKS = {
    "": "Select a functional block...",
    "communications_marketing": "Communications and Marketing",
    "legal_services": "Legal Services",
    "office_management": "Office Management",
    "financial_management": "Financial Management",
    "human_resources": "Human Resources",
    "records_management": "Records Management",
    "learner_administration": "Learner Administration",
    "university_governance": "University Governance",
}

# Sub-categories for CPE Internal blocks
CPE_INTERNAL_SUBCATEGORIES = {
    "office_management": {
        "": "Select sub-category...",
        "General": "General",
        "Policies and Procedures": "Policies and Procedures",
        "Communications": "Communications",
        "Staff Meetings": "Staff Meetings",
        "Trackers and Lists": "Trackers and Lists",
        "Canvas Catalog": "Canvas Catalog",
        "Course Resources": "Course Resources",
        "Email": "Email",
        "Letters": "Letters",
        "Presentations": "Presentations",
    },
    "financial_management": {
        "": "Select sub-category...",
        "Accounting": "Accounting",
        "Budget": "Budget",
        "Procurement and Contract Management": "Procurement and Contract Management",
    },
    "learner_administration": {
        "": "Select sub-category...",
        "Admissions": "Admissions",
        "Enrolment and Registration": "Enrolment and Registration",
        "Final Standing and Results": "Final Standing and Results",
        "Learner Accounts": "Learner Accounts",
    },
}

# Partner-level functional blocks for Definition & Approvals
DEFINITION_APPROVALS_BLOCKS = {
    "": "Select file type...",
    "Market Research": "Market Research",
    "Course Development": "Course Development",
    "Proposals and Approvals": "Proposals and Approvals",
    "Resources and Templates": "Resources and Templates",
}

# Partner-level functional blocks for Production & Delivery
PRODUCTION_DELIVERY_BLOCKS = {
    "": "Select file type...",
    "Budget": "Budget",
    "Communications and Marketing": "Communications and Marketing",
    "Instructor Contracts": "Instructor Contracts",
    "Course Management": "Course Management",
    "Course and Curricular Development": "Course and Curricular Development",
    "Resources and Templates": "Resources and Templates",
}

# Help content for Manual Generator tab
HELP_CONTENT = {
    "subject": {
        "title": "Subject/Activity (Required)",
        "content": "The main topic or activity the document covers. Use PascalCase formatting (capitalize the first letter of each word with no spaces). Examples: NamingConventions, RecordsManagement, CourseEvaluation",
    },
    "date": {
        "title": "Date (Required)",
        "content": "The date when the document was created or last modified. Will be formatted as YYYY-MM-DD according to ISO 8601 standard. Example: 2025-05-28",
    },
    "revisionStatus": {
        "title": "Revision Status (Required)",
        "content": "Indicates the version and status: Letters (A, B, C) for drafts, Numbers (0, 1, 2) for final versions, Combinations (0A, 0B) for drafts after final version",
    },
    "projectCode": {
        "title": "Project/Account Number (Optional)",
        "content": "A control number, project code, or account identifier that helps organize documents. Examples: CPE, PROJ2024, ACC-001",
    },
    "documentForm": {
        "title": "Document Form (Optional)",
        "content": "Three-letter code indicating the type of document. Common forms: AGD (Agenda), RPT (Report), GUI (Guidelines), PRS (Presentation), MNL (Manual)",
    },
    "facultySchool": {
        "title": "Faculty-School (Course Format)",
        "content": "Identifies the faculty and school using a dash separator. Examples: FHSD-SoN (Faculty of Health & Social Development - School of Nursing)",
    },
    "courseCode": {
        "title": "Course Code (Course Format)",
        "content": "Four-digit course number followed by four-digit section code, separated by a dash. Format: ####-#### Examples: 0386-0001",
    },
    "termOffered": {
        "title": "Term Offered (Course Format)",
        "content": "Academic term using format YYYYST where YYYY = Year, S = Session (W=Winter, S=Summer), T = Term (1, 2). Examples: 2024WT1, 2025ST1",
    },
}

# Help content for File Location tab
FILE_LOCATION_HELP = {
    "partner_related": {
        "title": "Partner-Related vs CPE Internal",
        "content": """**Partner-Related:** Files tied to a specific faculty/school partnership and their courses/programs. Examples: course budgets, instructor contracts, program marketing materials.

**CPE Internal:** Files about running CPE as a unit, not tied to any specific partner. Examples: staff meeting minutes, CPE policies, annual reports.""",
    },
    "definition_vs_production": {
        "title": "Definition & Approvals vs Production & Delivery",
        "content": """**Definition & Approvals:** Use for files about getting a program started - market research, proposals, approvals, initial course development.

**Production & Delivery:** Use for files about running an active program - budgets, marketing, instructor contracts, student materials.""",
    },
    "credential_vs_occurrence": {
        "title": "Credential Level vs Occurrence Level",
        "content": """**Credential Level:** Files that apply to ALL offerings of a credential (e.g., master syllabus, general program brochure).

**Occurrence Level:** Files specific to a particular term's offering (e.g., Fall 2024 attendance sheet, instructor contract for Winter 2025).""",
    },
}

# Document form keyword mapping for rule-based fallback
DOCUMENT_FORM_KEYWORDS = {
    "agenda": "AGD",
    "agreement": "AGR",
    "announcement": "ANN",
    "appendix": "APP",
    "attendance": "ATD",
    "budget": "BGT",
    "briefing note": "BRN",
    "concept paper": "CCP",
    "contract": "CON",
    "data set": "DAT",
    "dataset": "DAT",
    "fact sheet": "FCT",
    "form": "FRM",
    "grant": "GRA",
    "guidelines": "GUI",
    "guide": "GUI",
    "instruction": "INS",
    "interview": "INT",
    "invoice": "INV",
    "letter of attendance": "LAT",
    "letter of completion": "LCO",
    "legal": "LGL",
    "letter of participation": "LPA",
    "letter of proficiency": "LPR",
    "letter": "LTR",
    "minutes": "MIN",
    "manual": "MNL",
    "non-credit certificate": "NCC",
    "microcertificate": "NCM",
    "plan": "PLN",
    "policy": "POL",
    "procedure": "PRC",
    "sop": "PRC",
    "proposal": "PRO",
    "presentation": "PRS",
    "poster": "PST",
    "report": "RPT",
    "review": "RVW",
    "schedule": "SCH",
    "sample": "SMP",
    "survey": "SRY",
    "summary": "SUM",
    "template": "TEM",
    "timeline": "TML",
    "image": "IMG",
    "photo": "IMG",
    "screenshot": "SCR",
    "diagram": "DIA",
    "chart": "DIA",
}

# Faculty name patterns for rule-based extraction
FACULTY_PATTERNS = {
    "Irving K. Barber Faculty of Arts and Social Sciences": "IKBASS",
    "Irving K. Barber Faculty of Science": "IKBFOS",
    "Faculty of Creative and Critical Studies": "FCCS",
    "Okanagan School of Education": "OSE",
    "School of Engineering": "APSC-SoE",
    "Faculty of Applied Science": "APSC-SoE",
    "School of Nursing": "FHSD-SoN",
    "School of Social Work": "FHSD-SSW",
    "School of Health and Exercise Sciences": "FHSD-SHES",
    "Faculty of Health and Social Development": "FHSD",
    "Faculty of Management": "FoM",
    "Faculty of Medicine": "MED",
    "College of Graduate Studies": "CoGS",
}

# Supported file types for upload
SUPPORTED_FILE_TYPES = [
    "pdf", "docx", "doc", "xlsx", "xls", "csv", "txt",
    "jpg", "jpeg", "png", "gif",
]
