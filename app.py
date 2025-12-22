import streamlit as st
import anthropic
import base64
import re
import json
from datetime import datetime
from io import BytesIO

# PDF parsing
try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Word document parsing
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Excel parsing
try:
    import openpyxl
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False

# Image handling
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="UBC CPE File Naming Tool",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for UBC branding
st.markdown("""
<style>
    :root {
        --ubc-blue: #002145;
        --ubc-gold: #C1A01E;
    }

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

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #f0f0f0;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #002145 !important;
        color: white !important;
    }

    .output-box {
        background-color: #f8f8f8;
        border-left: 4px solid #C1A01E;
        padding: 15px;
        border-radius: 0 8px 8px 0;
        margin: 10px 0;
    }

    .file-suggestion {
        background-color: #e8f4f8;
        border: 1px solid #002145;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }

    .help-panel {
        background-color: #f8f8f8;
        border-left: 4px solid #C1A01E;
        padding: 15px;
        border-radius: 0 8px 8px 0;
    }
</style>
""", unsafe_allow_html=True)

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
    "DIA": "DIA - Diagram"
}

REVISION_STATUSES = {
    "A": "A - Initial draft sent for review",
    "B": "B - Official draft sent for external or internal review",
    "C": "C - Next incarnation of official draft",
    "0": "0 - First final revision",
    "0A": "0A - Draft after final has been produced",
    "0B": "0B - Draft after final has been produced",
    "0C": "0C - Draft after final has been produced",
    "1": "1 - Next revision after final"
}

FILE_EXTENSIONS = {
    "pdf": "pdf - Portable Document Format",
    "docx": "docx - Word Document",
    "xlsx": "xlsx - Excel Spreadsheet",
    "pptx": "pptx - PowerPoint Presentation",
    "txt": "txt - Text File",
    "csv": "csv - Comma Separated Values",
    "jpg": "jpg - JPEG Image",
    "png": "png - PNG Image"
}

HELP_CONTENT = {
    "subject": {
        "title": "Subject/Activity (Required)",
        "content": "The main topic or activity the document covers. Use PascalCase formatting (capitalize the first letter of each word with no spaces). Examples: NamingConventions, RecordsManagement, CourseEvaluation"
    },
    "date": {
        "title": "Date (Required)",
        "content": "The date when the document was created or last modified. Will be formatted as YYYY-MM-DD according to ISO 8601 standard. Example: 2025-05-28"
    },
    "revisionStatus": {
        "title": "Revision Status (Required)",
        "content": "Indicates the version and status: Letters (A, B, C) for drafts, Numbers (0, 1, 2) for final versions, Combinations (0A, 0B) for drafts after final version"
    },
    "projectCode": {
        "title": "Project/Account Number (Optional)",
        "content": "A control number, project code, or account identifier that helps organize documents. Examples: CPE, PROJ2024, ACC-001"
    },
    "documentForm": {
        "title": "Document Form (Optional)",
        "content": "Three-letter code indicating the type of document. Common forms: AGD (Agenda), RPT (Report), GUI (Guidelines), PRS (Presentation), MNL (Manual)"
    },
    "facultySchool": {
        "title": "Faculty-School (Course Format)",
        "content": "Identifies the faculty and school using a dash separator. Examples: FHSD-SoN (Faculty of Health & Social Development - School of Nursing)"
    },
    "courseCode": {
        "title": "Course Code (Course Format)",
        "content": "Four-digit course number followed by four-digit section code, separated by a dash. Format: ####-#### Examples: 0386-0001"
    },
    "termOffered": {
        "title": "Term Offered (Course Format)",
        "content": "Academic term using format YYYYST where YYYY = Year, S = Session (W=Winter, S=Summer), T = Term (1, 2). Examples: 2024WT1, 2025ST1"
    }
}


def sanitize_content(content: str, level: str = "medium") -> str:
    """Sanitize content based on privacy level."""
    if level == "low":
        return content[:3000]

    sanitized = content[:2000]

    if level in ["medium", "high"]:
        # Remove email addresses
        sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', sanitized)
        # Remove phone numbers
        sanitized = re.sub(r'(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', '[PHONE]', sanitized)
        # Remove SSN
        sanitized = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', sanitized)
        # Remove credit card numbers
        sanitized = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', sanitized)
        # Remove dollar amounts over $1000
        sanitized = re.sub(r'\$[0-9]{1,3}(,[0-9]{3})+(\.[0-9]{2})?', '[AMOUNT]', sanitized)
        # Remove Canadian postal codes
        sanitized = re.sub(r'\b[A-Za-z]\d[A-Za-z][-\s]?\d[A-Za-z]\d\b', '[POSTAL]', sanitized)
        # Remove SIN numbers
        sanitized = re.sub(r'\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b', '[SIN]', sanitized)

    if level == "high":
        # For high privacy, only keep first 500 chars
        sanitized = sanitized[:500]

    return sanitized


def read_pdf_content(file_bytes: bytes) -> str:
    """Extract text from PDF file."""
    if not PDF_AVAILABLE:
        return "PDF parsing not available"

    try:
        pdf_reader = PdfReader(BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages[:10]:  # Limit to first 10 pages
            text += page.extract_text() or ""
        return text[:4000]
    except Exception as e:
        return f"Could not extract PDF text: {str(e)}"


def read_docx_content(file_bytes: bytes) -> str:
    """Extract text from Word document."""
    if not DOCX_AVAILABLE:
        return "Word document parsing not available"

    try:
        doc = Document(BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text[:4000]
    except Exception as e:
        return f"Could not extract Word text: {str(e)}"


def read_xlsx_content(file_bytes: bytes) -> str:
    """Extract text from Excel file."""
    if not XLSX_AVAILABLE:
        return "Excel parsing not available"

    try:
        workbook = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True)
        text = ""
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            text += f"\nSheet: {sheet_name}\n"
            for row in sheet.iter_rows(max_row=50, values_only=True):
                row_text = " | ".join([str(cell) if cell else "" for cell in row])
                text += row_text + "\n"
        return text[:4000]
    except Exception as e:
        return f"Could not extract Excel text: {str(e)}"


def read_file_content(uploaded_file) -> tuple:
    """Read content from uploaded file. Returns (content, content_type)."""
    file_bytes = uploaded_file.read()
    file_name = uploaded_file.name.lower()

    if file_name.endswith('.pdf'):
        return read_pdf_content(file_bytes), "text"
    elif file_name.endswith('.docx'):
        return read_docx_content(file_bytes), "text"
    elif file_name.endswith(('.xlsx', '.xls')):
        return read_xlsx_content(file_bytes), "text"
    elif file_name.endswith(('.txt', '.csv')):
        return file_bytes.decode('utf-8', errors='ignore')[:4000], "text"
    elif file_name.endswith(('.jpg', '.jpeg', '.png', '.gif')):
        # For images, return base64 encoded data
        ext = file_name.split('.')[-1]
        mime_type = f"image/{ext}" if ext != 'jpg' else "image/jpeg"
        base64_data = base64.b64encode(file_bytes).decode('utf-8')
        return f"data:{mime_type};base64,{base64_data}", "image"
    else:
        return "Unsupported file type", "unknown"


def analyze_with_claude(api_key: str, content: str, file_name: str, content_type: str, privacy_level: str) -> dict:
    """Analyze file content with Claude API."""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        today = datetime.now().strftime("%Y-%m-%d")

        if content_type == "image":
            # Image analysis
            mime_type = content.split(';')[0].replace('data:', '')
            base64_data = content.split(',')[1]

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""I need help creating a CPE-compliant filename for this image.

IMPORTANT: First, carefully analyze what is shown in this image. Describe what you see in detail.

Based on what you observe, suggest an appropriate filename that accurately reflects the actual content.

Current filename: {file_name}

Key elements for the filename:
- Subject (required): What is actually shown in the image (use PascalCase)
- Document Form: Use IMG for photos, SCR for screenshots, DIA for diagrams
- Date: Use today's date {today} if no date is visible
- Revision: Use 'Rev0' for final version

Respond with ONLY a JSON object:
{{
    "suggestedName": "ActualContentDescription_IMG_{today}_Rev0.jpg",
    "reasoning": "I can see [specific description of what's in the image]",
    "confidence": 8,
    "detectedType": "IMG",
    "suggestedSubject": "SpecificContentInPascalCase"
}}"""
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": base64_data
                            }
                        }
                    ]
                }]
            )
        else:
            # Text document analysis
            sanitized_content = sanitize_content(content, privacy_level)

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": f"""You are a file naming expert for the University of British Columbia's Continuing Professional Education (CPE) department.

Analyze this file and suggest a CPE-compliant filename following these conventions:

BASIC FORMAT: Subject_Date_RevisionStatus.ext
ADVANCED FORMAT: ProjectCode_Subject_DocumentForm_Date_RevisionStatus.ext
COURSE FORMAT: FacultySchool_CourseCode_Term_DocumentForm_Date_RevisionStatus.ext

DOCUMENT FORMS (use 3-letter codes):
- AGD (Agenda), AGR (Agreement), ANN (Announcement), APP (Appendix)
- BGT (Budget), BRN (Briefing Note), CCP (Concept Paper), CON (Contract)
- DAT (Data Set), FCT (Fact Sheet), FRM (Form), GUI (Guidelines)
- INS (Instruction), LTR (Letter), MIN (Minutes), MNL (Manual)
- PLN (Plan), POL (Policy), PRC (Procedure), PRO (Proposal)
- PRS (Presentation), RPT (Report), RVW (Review), SCH (Schedule)
- SUM (Summary), TEM (Template), and others

REVISION STATUS:
- A, B, C for drafts
- 0 for first final version
- 1, 2, 3+ for subsequent revisions

Current file: {file_name}
Content preview: {sanitized_content}

Respond with ONLY a JSON object in this format:
{{
    "suggestedName": "RecommendedFileName_{today}_Rev0.pdf",
    "reasoning": "Brief explanation of naming choice",
    "confidence": 8,
    "detectedType": "document form detected",
    "suggestedSubject": "detected subject in PascalCase"
}}"""
                }]
            )

        # Parse response
        response_text = message.content[0].text

        # Try to extract JSON from the response
        try:
            # Find JSON in response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
                return {"success": True, "analysis": result}
        except json.JSONDecodeError:
            pass

        # Fallback if JSON parsing fails
        ext = file_name.split('.')[-1] if '.' in file_name else 'pdf'
        return {
            "success": True,
            "analysis": {
                "suggestedName": f"Document_{today}_Rev0.{ext}",
                "reasoning": "AI analysis completed but response format was unclear",
                "confidence": 5,
                "detectedType": "unknown",
                "suggestedSubject": "Document"
            }
        }

    except anthropic.AuthenticationError:
        return {"success": False, "error": "Invalid API key. Please check your Claude API key."}
    except anthropic.RateLimitError:
        return {"success": False, "error": "Rate limit exceeded. Please wait a moment and try again."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_filename(format_type: str, subject: str, date_val: datetime, revision: str,
                     extension: str, project_code: str = "", document_form: str = "",
                     faculty_school: str = "", course_code: str = "", term: str = "") -> tuple:
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


# Main app header
st.markdown("""
<div class="main-header">
    <h1>UBC CPE File Naming Tool <span class="version-badge">V2 Web</span></h1>
    <p style="color: #666;">Generate standardized filenames and analyze files with AI</p>
</div>
""", unsafe_allow_html=True)

# Main tabs
tab1, tab2 = st.tabs(["📝 Manual Generator", "🤖 AI File Analyzer"])

# ==================== MANUAL GENERATOR TAB ====================
with tab1:
    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown('<div class="help-panel">', unsafe_allow_html=True)
        st.subheader("Field Guide")

        help_topic = st.selectbox(
            "Select a field to learn more:",
            [""] + list(HELP_CONTENT.keys()),
            format_func=lambda x: HELP_CONTENT[x]["title"] if x else "Select a field..."
        )

        if help_topic:
            st.info(f"**{HELP_CONTENT[help_topic]['title']}**\n\n{HELP_CONTENT[help_topic]['content']}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Format selector
        st.subheader("Choose Naming Format")
        format_type = st.radio(
            "Format",
            ["basic", "advanced", "course"],
            format_func=lambda x: {
                "basic": "Basic Format - For simple documents",
                "advanced": "Advanced Format - For departmental/project documents",
                "course": "Course-Specific Format - For educational materials"
            }[x],
            horizontal=True
        )

        st.divider()

        # Form fields
        col_a, col_b = st.columns(2)

        with col_a:
            subject = st.text_input(
                "Subject/Activity *",
                placeholder="e.g., NamingConventions",
                help="Use PascalCase (capitalize first letter of each word, no spaces)"
            )
            # Auto-format subject
            if subject:
                subject = re.sub(r'\s+', '', subject)
                if subject:
                    subject = subject[0].upper() + subject[1:]

            date_val = st.date_input("Date *", value=datetime.now())

            revision = st.selectbox(
                "Revision Status *",
                list(REVISION_STATUSES.keys()),
                format_func=lambda x: REVISION_STATUSES[x],
                index=3  # Default to "0"
            )

        with col_b:
            extension = st.selectbox(
                "File Extension",
                list(FILE_EXTENSIONS.keys()),
                format_func=lambda x: FILE_EXTENSIONS[x]
            )

            # Advanced fields
            if format_type in ["advanced", "course"]:
                project_code = st.text_input(
                    "Project/Account Number",
                    placeholder="e.g., CPE",
                    help="Optional: Control number, project code, or account identifier"
                )

                document_form = st.selectbox(
                    "Document Form",
                    list(DOCUMENT_FORMS.keys()),
                    format_func=lambda x: DOCUMENT_FORMS[x]
                )
            else:
                project_code = ""
                document_form = ""

            # Course-specific fields
            if format_type == "course":
                faculty_school = st.text_input(
                    "Faculty-School",
                    placeholder="e.g., FHSD-SoN",
                    help="Use dash to separate faculty and school"
                )

                course_code = st.text_input(
                    "Course Code",
                    placeholder="e.g., 0386-0001",
                    help="Four-digit number followed by four-digit section code"
                )

                term = st.text_input(
                    "Term Offered",
                    placeholder="e.g., 2024WT2",
                    help="Format: YYYYST (Year + Session + Term)"
                )
            else:
                faculty_school = ""
                course_code = ""
                term = ""

        # Generate button
        if st.button("Generate Filename", type="primary", use_container_width=True):
            if not subject or not date_val or not revision:
                st.error("Please fill in all required fields (Subject, Date, and Revision Status).")
            else:
                standard_name, sharepoint_name = generate_filename(
                    format_type, subject, date_val, revision, extension,
                    project_code, document_form, faculty_school, course_code, term
                )

                st.markdown('<div class="output-box">', unsafe_allow_html=True)
                st.subheader("Generated Filename")

                # Standard filename
                st.text_input("CPE Standard Filename:", value=standard_name, key="standard_output")
                char_count = len(standard_name)
                if char_count > 150:
                    st.error(f"⚠️ {char_count} characters - Too long! May cause system issues")
                elif char_count > 100:
                    st.warning(f"⚠️ {char_count} characters - Consider shortening")
                else:
                    st.success(f"✓ {char_count} characters")

                # SharePoint filename
                st.text_input("SharePoint Filename (spaces):", value=sharepoint_name, key="sharepoint_output")

                st.markdown('</div>', unsafe_allow_html=True)


# ==================== AI FILE ANALYZER TAB ====================
with tab2:
    col1, col2 = st.columns([2, 1])

    with col2:
        st.subheader("Claude AI Settings")

        # API Key input
        api_key = st.text_input(
            "Claude API Key",
            type="password",
            placeholder="sk-ant-...",
            help="Your Anthropic API key"
        )

        # Check for API key in secrets (for Streamlit Cloud)
        if not api_key:
            try:
                api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
            except Exception:
                pass

        # Privacy controls
        st.subheader("Privacy Protection")
        privacy_level = st.selectbox(
            "Privacy Level",
            ["high", "medium", "low"],
            index=1,
            format_func=lambda x: {
                "high": "🛡️ Maximum Privacy",
                "medium": "⚖️ Balanced",
                "low": "📄 Full Content"
            }[x]
        )

        privacy_descriptions = {
            "high": "Sends only document structure and keywords. Maximum privacy.",
            "medium": "Removes sensitive info (emails, phone, addresses) before sending.",
            "low": "Sends full document content. Best analysis quality."
        }
        st.info(privacy_descriptions[privacy_level])

        # How it works
        st.subheader("How it works:")
        st.markdown("""
        1. Upload files below
        2. Choose privacy level
        3. Claude AI analyzes content
        4. Get CPE-compliant name suggestions
        """)

        st.info("**Note:** Analysis costs approximately $0.005 per file.")

    with col1:
        st.subheader("Upload Files")

        # File uploader
        uploaded_files = st.file_uploader(
            "Drop files here or click to browse",
            type=['pdf', 'docx', 'doc', 'xlsx', 'xls', 'csv', 'txt', 'jpg', 'jpeg', 'png', 'gif'],
            accept_multiple_files=True,
            help="Supported: PDF, Word, Excel, CSV, TXT, and images"
        )

        if uploaded_files:
            st.write(f"**{len(uploaded_files)} file(s) selected**")

            # Display file list
            for i, file in enumerate(uploaded_files):
                with st.expander(f"📄 {file.name}", expanded=False):
                    st.write(f"Size: {file.size / 1024:.2f} KB")
                    st.write(f"Type: {file.type}")

            # Analyze button
            if st.button("🤖 Analyze Files with Claude AI", type="primary", use_container_width=True):
                if not api_key:
                    st.error("Please enter your Claude API key in the sidebar or configure it in Streamlit secrets.")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    results = []

                    for i, file in enumerate(uploaded_files):
                        status_text.text(f"Analyzing {file.name}... ({i+1}/{len(uploaded_files)})")
                        progress_bar.progress((i + 1) / len(uploaded_files))

                        # Read file content
                        file.seek(0)  # Reset file pointer
                        content, content_type = read_file_content(file)

                        if content_type == "unknown":
                            results.append({
                                "file": file.name,
                                "success": False,
                                "error": "Unsupported file type"
                            })
                            continue

                        # Analyze with Claude
                        result = analyze_with_claude(api_key, content, file.name, content_type, privacy_level)
                        result["file"] = file.name
                        results.append(result)

                    status_text.text("Analysis complete!")

                    # Display results
                    st.subheader("Results")

                    for result in results:
                        if result.get("success"):
                            analysis = result["analysis"]
                            st.markdown(f"""
                            <div class="file-suggestion">
                                <h4>📄 {result['file']}</h4>
                                <p><strong>Suggested Name:</strong> <code>{analysis['suggestedName']}</code></p>
                                <p><strong>Reasoning:</strong> {analysis['reasoning']}</p>
                                <p><strong>Confidence:</strong> {analysis.get('confidence', 'N/A')}/10</p>
                                <p><strong>Detected Type:</strong> {analysis.get('detectedType', 'N/A')}</p>
                            </div>
                            """, unsafe_allow_html=True)

                            # Copy button
                            st.text_input(
                                "Copy suggested name:",
                                value=analysis['suggestedName'],
                                key=f"copy_{result['file']}"
                            )
                        else:
                            st.error(f"❌ **{result['file']}**: {result.get('error', 'Unknown error')}")
        else:
            st.info("👆 Upload files to get started with AI analysis")


# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>UBC CPE File Naming Tool | Powered by Claude AI</p>
    <p>For use by UBC Continuing Professional Education staff</p>
</div>
""", unsafe_allow_html=True)
