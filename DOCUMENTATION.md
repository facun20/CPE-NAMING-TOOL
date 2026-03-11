# UBC CPE File Naming Tool — Complete Documentation

> A comprehensive guide to the tool's architecture, features, and setup for desktop/local development.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Project Structure](#2-project-structure)
3. [Setup & Installation](#3-setup--installation)
4. [Configuration](#4-configuration)
5. [Features](#5-features)
6. [Module Reference](#6-module-reference)
7. [PII Stripping](#7-pii-stripping)
8. [AI Analysis Providers](#8-ai-analysis-providers)
9. [Filename Generation](#9-filename-generation)
10. [File Location Navigator](#10-file-location-navigator)
11. [Testing](#11-testing)
12. [Deployment](#12-deployment)
13. [Change Log](#13-change-log)

---

## 1. Project Overview

The **UBC CPE File Naming Tool** is a Streamlit application that helps CPE staff:

- Generate standardized filenames in 3 formats (Basic, Advanced, Course)
- Navigate the CPE/Partner folder hierarchy to find correct file locations
- Use AI (Gemini free, Claude paid, or offline) to auto-analyze documents and suggest filenames
- Strip PII from document content before sending to external AI providers
- Track usage analytics and manage reusable naming templates

**Tech Stack:** Python 3.11+, Streamlit, Anthropic SDK, OpenRouter API, Microsoft Presidio, spaCy, PyMuPDF, python-docx, openpyxl

---

## 2. Project Structure

```
CPE-NAMING-TOOL/
├── app.py                    # Main Streamlit app (orchestrator)
├── constants.py              # Data models, codes, configurations
├── filename_generator.py     # Filename generation + input validation
├── file_location.py          # Folder path generation (decision tree)
├── file_processing.py        # File content extraction (PDF, Word, Excel, images)
├── ai_analysis.py            # AI analysis (Claude, Gemini, rule-based)
├── pii_scrubber.py           # PII detection and redaction (Presidio)
├── ui_components.py          # Templates, analytics, export, CSS
├── config.toml               # Streamlit theme configuration
├── requirements.txt          # Python dependencies
├── secrets.toml.example      # API key template
├── README.md                 # User-facing docs
├── DOCUMENTATION.md          # This file
├── tests/
│   ├── test_filename_generator.py   # 21 tests
│   ├── test_file_location.py        # 9 tests
│   ├── test_ai_analysis.py          # 18 tests
│   ├── test_pii_scrubber.py         # 13 tests
│   ├── test_ui_components.py        # 20 tests
│   └── __init__.py
└── .devcontainer/
    └── devcontainer.json     # VS Code Dev Container config
```

---

## 3. Setup & Installation

### Local Desktop Setup

```bash
# Clone the repo
git clone <repo-url>
cd CPE-NAMING-TOOL

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (required for PII stripping)
python -m spacy download en_core_web_lg

# Run the app
streamlit run app.py
# Opens at http://localhost:8501
```

### Streamlit Cloud Setup

The spaCy model is included directly in `requirements.txt` as a pip URL — no extra steps needed. Just:

1. Push to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Add API keys in the Streamlit Cloud Secrets UI

### Dev Container (VS Code / Codespaces)

Open the project in VS Code — the `.devcontainer/devcontainer.json` will auto-configure Python 3.11 with all dependencies.

---

## 4. Configuration

### API Keys (`secrets.toml` or Streamlit Cloud Secrets)

Create `.streamlit/secrets.toml` locally:

```toml
# Required for Gemini AI analysis (FREE)
OPENROUTER_API_KEY = "sk-or-v1-..."

# Optional for Claude AI analysis (PAID, ~$0.005/file)
ANTHROPIC_API_KEY = "sk-ant-..."

# Optional authentication
# AUTH_ENABLED = true
# [USERS]
# admin = "your-password"
```

### Streamlit Theme (`config.toml`)

```toml
[theme]
primaryColor = "#002145"              # UBC Navy Blue
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F8F8F8"
textColor = "#333333"
font = "sans serif"

[server]
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

### Key Constants (in `constants.py`)

| Constant | Value | Purpose |
|----------|-------|---------|
| `MAX_TEXT_CONTENT` | 4000 chars | Max text sent to AI |
| `MAX_EXCEL_CONTENT` | 6000 chars | Max Excel content to AI |
| `MAX_PDF_PAGES` | 10 | PDF page limit for processing |
| `PDF_DPI` | 150 | PDF-to-image resolution |
| `MAX_SUBJECT_LENGTH` | 50 chars | Subject field limit |
| `FILENAME_WARN_LENGTH` | 100 chars | Length warning threshold |
| `FILENAME_ERROR_LENGTH` | 150 chars | Length error threshold |
| `GEMINI_MODEL` | `google/gemini-2.5-flash` | Free AI model |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Paid AI model |

---

## 5. Features

### 5.1 Manual Filename Generator (Tab 1)

**Three naming formats:**

| Format | Pattern | Use Case |
|--------|---------|----------|
| **Basic** | `Subject_Date_RevisionStatus.ext` | General documents |
| **Advanced** | `ProjectCode_Subject_DocumentForm_Date_RevisionStatus.ext` | Project-specific docs |
| **Course** | `Faculty-School_CourseCode_Term_Subject_DocumentForm_Date_RevisionStatus.ext` | Academic documents |

**Validation:** Real-time validation on all fields (PascalCase subjects, `####-####` course codes, `YYYYST` terms). Character count warnings at 100/150 chars.

**Templates:** 6 built-in templates + save/load custom templates.

**SharePoint mode:** Generates space-separated filenames for SharePoint compatibility.

### 5.2 File Location Navigator (Tab 2)

Decision-tree questionnaire that builds folder paths:

- **CPE Internal:** 8 functional blocks (Communications, Legal, Office Management, Financial, HR, Records, Learner Admin, Governance) with sub-categories
- **Partner-Related:** 12 Faculty-School codes → Phase (Definition & Approvals / Production & Delivery) → file types with occurrence codes

Outputs breadcrumb paths (`→` separated) and folder paths (`/` separated).

### 5.3 AI File Analyzer (Tab 3)

- Upload documents (PDF, Word, Excel, CSV, TXT, JPG, PNG, GIF)
- Choose AI provider: **Gemini (free)**, **Claude (paid)**, or **Offline (rule-based)**
- PII is automatically stripped before sending to AI
- Batch processing with CSV export
- Smart caching (MD5 hash) prevents re-analyzing identical files
- Confidence scores: High (green, 8-10), Medium (orange, 5-7), Low (red, 0-4)

### 5.4 Session Dashboard (Tab 4)

- Usage statistics (filenames generated, locations generated, files analyzed)
- Format usage breakdown
- AI provider statistics
- Custom template management
- Session duration tracking

---

## 6. Module Reference

### `app.py` — Orchestrator

Entry point. Initializes session state, renders tabs, delegates to specialized modules. Handles optional authentication.

### `constants.py` — Data Models

All static data: 60+ document form codes, 12 faculty-school codes, 8 CPE functional blocks, revision statuses, file extensions, help text, pattern keywords for rule-based detection.

### `filename_generator.py` — Generation & Validation

| Function | Purpose |
|----------|---------|
| `generate_filename()` | Creates standard + SharePoint filenames |
| `validate_subject()` | PascalCase, max 50 chars, alphanumeric + hyphens |
| `validate_course_code()` | `####-####` format |
| `validate_term()` | `YYYYST` format (e.g., `2024WT2`) |
| `validate_project_code()` | Max 20 chars |
| `validate_faculty_school()` | Known code check |
| `check_filename_length()` | Warning/error thresholds |

### `file_location.py` — Path Generation

`generate_file_location_path()` — Takes user selections (partner/internal, functional block, phase, etc.) and builds breadcrumb + folder paths.

### `file_processing.py` — Content Extraction

| Function | Purpose |
|----------|---------|
| `read_file_content()` | Dispatcher for all file types |
| `read_pdf_content()` | PyPDF2 text extraction |
| `pdf_to_image()` | PyMuPDF PDF → PNG conversion |
| `read_docx_content()` | Word paragraph extraction |
| `read_xlsx_content()` | Excel with sheet/column structure |
| `image_to_base64()` | Image → base64 data URI |
| `compute_file_hash()` | MD5 for caching |

### `ai_analysis.py` — Multi-Provider AI

| Function | Purpose |
|----------|---------|
| `analyze_with_claude()` | Anthropic API (paid) |
| `analyze_with_gemini()` | OpenRouter → Gemini (free) |
| `analyze_with_rules()` | Offline pattern matching |
| `get_confidence_level()` | Score → level/color/message |

All providers return consistent JSON with: suggested name, format, faculty, course code, term, subject, document form, date, revision, reasoning, confidence.

### `pii_scrubber.py` — Privacy Protection

| Function | Purpose |
|----------|---------|
| `scrub_text()` | Main scrubber (Presidio or fallback regex) |
| `get_pii_summary()` | Aggregates detected PII by type |
| `is_available()` | Checks if Presidio + spaCy model is loaded |

### `ui_components.py` — UI Utilities

Templates (save/load/delete), analytics tracking, CSV export, result persistence, CSS styling (UBC branding), accessibility HTML.

---

## 7. PII Stripping

### How It Works

```
Document Content
       ↓
  scrub_text()
       ↓
  Presidio available? ─── YES → Full NER detection (spaCy)
       │                          Names, emails, phones, SINs,
       │                          credit cards, IPs, student/employee IDs
       │
       └── NO → Fallback regex detection
                 Emails, phones, SINs, credit cards, IPs
       ↓
  Redacted text (e.g., "John Smith" → "<PERSON>")
       ↓
  Safe to send to AI APIs
```

### Detected PII Types

| Entity | Presidio | Fallback Regex |
|--------|----------|----------------|
| Person names | Yes | No |
| Email addresses | Yes | Yes |
| Phone numbers | Yes | Yes |
| Canadian SINs | Yes (custom) | Yes |
| Credit cards | Yes | Yes |
| IP addresses | Yes | Yes |
| Student IDs | Yes (custom) | No |
| Employee IDs | Yes (custom) | No |
| Dates/DOBs | Yes | No |
| Locations | Yes | No |

### Desktop Setup for PII

```bash
pip install presidio-analyzer presidio-anonymizer spacy
python -m spacy download en_core_web_lg
```

If the spaCy model is missing, the tool falls back to regex-based scrubbing automatically — no crash, just reduced detection.

---

## 8. AI Analysis Providers

| Provider | Cost | API Key | How It Works |
|----------|------|---------|--------------|
| **Gemini** | Free | `OPENROUTER_API_KEY` | Routes through OpenRouter to Google Gemini 2.5 Flash |
| **Claude** | ~$0.005/file | `ANTHROPIC_API_KEY` | Direct Anthropic API call to Claude Sonnet |
| **Offline** | Free | None | Rule-based pattern matching using keywords from `constants.py` |

All providers receive the same structured prompt and return standardized JSON. PDFs are converted to images for better OCR/vision analysis when using AI providers.

---

## 9. Filename Generation

### Revision Status Codes

| Code | Meaning |
|------|---------|
| A | Initial draft |
| B | Official draft |
| C | Next draft |
| 0 | First final version |
| 1, 2 | Subsequent revisions |
| 0A, 0B, 0C | Drafts after first final |

### Document Form Codes (60+ types)

**Examples:** `AGR` (Agreement), `BGT` (Budget), `GUI` (Guideline), `POL` (Policy), `TEM` (Template), `RPT` (Report), `MIN` (Minutes), `LTR` (Letter), `SCH` (Schedule), `DAT` (Dataset)

Full list in `constants.py`.

### Term Format: `YYYYST`

- `YYYY` = Academic year
- `S` = Session: `W` (Winter Sep-Apr) or `S` (Summer May-Aug)
- `T` = Term: `1` or `2`

Examples: `2024WT1` (Winter Term 1), `2025ST2` (Summer Term 2)

### Faculty-School Codes

| Code | Faculty/School |
|------|---------------|
| IKBASS | Irving K. Barber Faculty of Arts and Social Sciences |
| IKBFOS | Irving K. Barber Faculty of Science |
| FCCS | Faculty of Creative and Critical Studies |
| OSE | Okanagan School of Education |
| APSC-SoE | Applied Science - School of Engineering |
| FHSD-SoN | Health & Social Dev - School of Nursing |
| FHSD-SSW | Health & Social Dev - School of Social Work |
| FHSD-SHES | Health & Social Dev - School of Health & Exercise Sciences |
| FoM | Faculty of Management |
| MED | Faculty of Medicine |
| CoGS | College of Graduate Studies |

---

## 10. File Location Navigator

### CPE Internal Blocks

1. Communications and Marketing
2. Legal Services
3. Office Management (11 sub-categories)
4. Financial Management (3 sub-categories)
5. Human Resources
6. Records Management
7. Learner Administration (4 sub-categories)
8. University Governance

### Partner-Related Paths

```
Partner (Faculty-School)
  └─ Definition & Approvals
  │    └─ Subject Area → File Type
  └─ Production & Delivery
       └─ Credential/Program
            ├─ All offerings (credential-level)
            └─ Specific term (occurrence-level, YYYYST code)
                 └─ File Type
```

---

## 11. Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module
pytest tests/test_filename_generator.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing
```

**81 total tests** across 5 modules covering filename generation, file location paths, AI analysis, PII scrubbing, and UI components.

---

## 12. Deployment

### Local Desktop

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_lg
streamlit run app.py
```

### Streamlit Cloud

1. Push to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Add secrets (API keys) in the Streamlit Cloud dashboard
4. The spaCy model installs automatically via the pip URL in `requirements.txt`

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

---

## 13. Change Log

| Commit | Description |
|--------|-------------|
| `7ab7ebd` | Add spaCy model to requirements for Streamlit Cloud |
| `16081b3` | Fix PII stripping hanging when spaCy model is missing |
| `f321343` | Add PII stripping with Microsoft Presidio |
| `e77b1cb` | Major refactor: modularize codebase + 16 improvements |
| `5ba20ac` | Refactor breadcrumb and subject area handling |
| `1f01b3d` | Enhance UI and add file location functionality |
| `606c2d5` | Update API key variable in OpenRouter request |
| `15b7381` | Refactor OpenRouter API key input method |
| `50d47d3` | Revise filename conventions for subjects and formats |
| `c260ccc` | Improve Excel content extraction method |
| `fe637de` | Refactor PDF analysis prompts for clarity |
| `a9747ad` | Improve PDF parsing and image conversion |
| `f1403e8` | Add requests and PyMuPDF to requirements |
| `d50d3b5` | Implement document form detection and naming format |
| `d0f270a` | Add UBC CPE File Naming Tool functionality |
| `395385b` | Refactor Gemini API integration to use OpenRouter |
| `e11880a` | Refactor privacy handling |
| `e5d7ab7` | Upgrade Gemini API model and improve error handling |
