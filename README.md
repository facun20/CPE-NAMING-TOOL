# UBC CPE File Naming Tool

A Streamlit web application for UBC Continuing Professional Education (CPE) staff to generate standardized filenames, navigate file locations, and analyze documents with AI.

## Features

### Manual Filename Generator
- **Three naming formats:** Basic, Advanced, and Course-specific
- **Real-time validation** on all input fields (course codes, terms, subjects)
- **Character count warnings** for filenames exceeding recommended lengths
- **SharePoint-compatible** filenames (with spaces instead of underscores)
- **Template system** — save and reuse frequently-used naming configurations
- **Clear/reset** buttons for quick form clearing

### File Location Navigator
- **Decision-tree questionnaire** guides users to the correct folder
- **Partner-related** paths (Definition & Approvals, Production & Delivery)
- **CPE Internal** paths with functional block sub-categories
- **Occurrence code builder** for term-specific file placement
- **Breadcrumb navigation** and copyable folder paths

### AI File Analyzer
- **Gemini (FREE)** via OpenRouter — no cost for analysis
- **Claude (Paid)** — higher accuracy, approximately $0.005 per file
- **Offline mode** — rule-based pattern matching, no API key required
- **Batch processing** — analyze multiple files at once
- **CSV export** — download all results as a spreadsheet
- **Smart caching** — identical files aren't re-analyzed
- **Confidence scores** — color-coded (green/orange/red) with review recommendations
- **Result persistence** — results survive tab switches within a session
- Supports: PDF, Word, Excel, CSV, TXT, JPG, PNG, GIF

### Session Dashboard
- **Usage analytics** — track formats used, partners, document types
- **AI provider statistics** — see which provider you're using most
- **Custom template management** — view and delete saved templates

### Additional Features
- **Authentication** — optional username/password login (configurable via secrets)
- **Accessibility** — skip-to-content link, focus indicators, keyboard navigation
- **UBC branding** — navy blue (#002145) and gold (#C1A01E) theme

## Quick Start

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd CPE-NAMING-TOOL

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

### Configuration

#### API Keys (for AI analysis)

Copy the example secrets file and add your keys:

```bash
cp secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
# Free - get at https://openrouter.ai/keys
OPENROUTER_API_KEY = "sk-or-v1-your-key-here"

# Optional paid - get at https://console.anthropic.com
ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

You can also enter API keys directly in the app UI.

#### Authentication (Optional)

Add to `.streamlit/secrets.toml` to enable login:

```toml
AUTH_ENABLED = true

[USERS]
admin = "your-password"
staff1 = "another-password"
```

### Dev Container

A `.devcontainer/devcontainer.json` is included for VS Code / GitHub Codespaces development.

## Project Structure

```
CPE-NAMING-TOOL/
├── app.py                  # Main Streamlit application (thin orchestrator)
├── constants.py            # All data models, codes, and configuration
├── filename_generator.py   # Filename generation and input validation
├── file_location.py        # File location path generation
├── file_processing.py      # File content extraction (PDF, Word, Excel, images)
├── ai_analysis.py          # AI analysis (Claude, Gemini, rule-based fallback)
├── ui_components.py        # Templates, analytics, export, CSS/styling
├── config.toml             # Streamlit theme configuration
├── requirements.txt        # Python dependencies
├── secrets.toml.example    # API key template
├── tests/
│   ├── test_filename_generator.py
│   ├── test_file_location.py
│   ├── test_ai_analysis.py
│   └── test_ui_components.py
└── .devcontainer/
    └── devcontainer.json
```

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

## Naming Convention Reference

### Formats

| Format | Pattern | Example |
|--------|---------|---------|
| Basic | `Subject_Date_RevisionStatus.ext` | `NamingConventions_2025-03-15_Rev0.pdf` |
| Advanced | `ProjectCode_Subject_DocumentForm_Date_RevisionStatus.ext` | `CPE_RecordsManagement_POL_2025-01-20_Rev0.pdf` |
| Course | `Faculty-School_CourseCode_Term_Subject_DocumentForm_Date_RevisionStatus.ext` | `FHSD-SoN_0386-0001_2024WT2_TEM_2025-01-10_Rev0.pptx` |

### Revision Status Codes

| Code | Meaning |
|------|---------|
| A, B, C | Draft versions |
| 0, 1, 2 | Final versions |
| 0A, 0B | Drafts after first final |

### Term Format

`YYYYST` where:
- YYYY = Year
- S = Session (W=Winter Sept-Apr, S=Summer May-Aug)
- T = Term (1 or 2)

Example: `2024WT1` = Winter 2024, Term 1 (September-December)

## Deployment

### Streamlit Cloud

1. Push to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Add API keys in Streamlit Cloud's Secrets management

### Docker (optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

## License

For use by UBC Continuing Professional Education staff.
