"""
AI analysis module for the UBC CPE File Naming Tool.

Supports Claude (paid) and Gemini (free via OpenRouter) for document analysis,
with a rule-based fallback when AI is unavailable. Includes caching to avoid
redundant API calls and confidence-based result classification.
"""

import re
import json
from datetime import datetime

from constants import (
    OPENROUTER_BASE_URL,
    GEMINI_MODEL,
    CLAUDE_MODEL,
    MAX_TEXT_CONTENT,
    MAX_EXCEL_CONTENT,
    DOCUMENT_FORM_KEYWORDS,
    FACULTY_PATTERNS,
)

# ─── System prompt (shared between Claude and Gemini) ──────────────────────

SYSTEM_PROMPT = """You are a file naming expert for UBC CPE (Continuing Professional Education) at UBC Okanagan. Your role is to analyze documents and generate standardized filenames following CPE naming conventions.

IMPORTANT RULES:
- Always respond with ONLY a valid JSON object — no markdown, no code blocks, no extra text.
- Be precise: only extract fields you can confirm from the document content.
- Never invent Faculty-School codes. Only use codes from the provided list if you see exact matches.
- Subject must use Title-Kebab-Case and be MAX 50 characters.
- When uncertain, prefer the Basic format and set confidence lower.
- Date should be YYYY-MM-DD format. Use today's date if none found in document.
- Revision defaults to Rev0 for final, RevA for drafts."""


def _build_analysis_prompt(file_name: str, today: str, content_type: str, is_pdf: bool = False) -> str:
    """Build the analysis prompt for AI providers."""
    if content_type == "image" and is_pdf:
        return f"""READ ALL TEXT in this PDF document image carefully.

Current filename: {file_name}
Today's date: {today}

=== STEP 1: EXTRACT ALL AVAILABLE FIELDS ===

1. FACULTY-SCHOOL (use dash between Faculty and School):
   UBC Okanagan Faculties & Schools - use these abbreviations:
   - "Irving K. Barber Faculty of Arts and Social Sciences" → IKBASS
   - "Irving K. Barber Faculty of Science" → IKBFOS (or IKB-FOS if with school)
   - "Faculty of Creative and Critical Studies" → FCCS
   - "Okanagan School of Education" → OSE
   - "Faculty of Applied Science" / "School of Engineering" → APSC-SoE
   - "Faculty of Health and Social Development" → FHSD
     - with "School of Nursing" → FHSD-SoN
     - with "School of Social Work" → FHSD-SSW
     - with "School of Health and Exercise Sciences" → FHSD-SHES
   - "Faculty of Management" → FoM
   - "Faculty of Medicine" → MED
   - "College of Graduate Studies" → CoGS

   FORMAT: Faculty-School with dash (e.g., FHSD-SoN, APSC-SoE)
   If only Faculty found (no specific school), just use Faculty code (e.g., FCCS)

2. COURSE CODE - Four digits + dash + four digits (e.g., 0386-0001)
   Look for course numbers, section codes

3. TERM OFFERED - Format: YYYYST (Year + Session + Term)
   - Session: W = Winter (Sept-Apr), S = Summer (May-Aug)
   - Term: 1 or 2
   - Sept-Dec → WT1 | Jan-Apr → WT2 | May-Jun → ST1 | Jul-Aug → ST2
   - Example: "December 2025" → 2025WT1
   - Example: "March 2026" → 2025WT2 (still Winter session)

4. PROJECT/ACCOUNT CODE - Project numbers, grant codes (e.g., CPE, PROJ2024)

5. SUBJECT - Use Title-Kebab-Case (e.g., Wildland-Fire-Ecology)
   MAX 50 CHARACTERS! Truncate at word boundary if longer.

6. DOCUMENT FORM codes:
   LETTERS & CERTIFICATES:
   - "Letter of Proficiency" → LPR | "Letter of Completion" → LCO
   - "Letter of Attendance" → LAT | "Letter of Participation" → LPA
   - "Non-Credit Certificate" → NCC | "MicroCertificate" → NCM

   COMMON TYPES:
   - Agenda → AGD | Agreement → AGR | Budget → BGT | Contract → CON
   - Form → FRM | Guidelines/Guide → GUI | Instructions → INS | Invoice → INV
   - Letter (general) → LTR | Minutes → MIN | Manual → MNL | Plan → PLN
   - Policy → POL | Procedure/SOP → PRC | Proposal → PRO | Presentation → PRS
   - Report → RPT | Schedule → SCH | Template → TEM | Summary → SUM

7. REVISION STATUS:
   - Draft: RevA, RevB, RevC (letters for drafts)
   - Final: Rev0 (first final), Rev1, Rev2 (subsequent finals)
   - Draft after final: Rev0A, Rev0B (number + letter)

=== STEP 2: CHOOSE FORMAT ===

COURSE FORMAT (Faculty + Course content):
Faculty-School_CourseCode_TermOffered_DocumentForm_Date_RevisionStatus.ext
Example: FHSD-SoN_0386-0001_2024WT2_TEM_2025-01-10_Rev0.pptx

ADVANCED FORMAT (Project code found):
ProjectCode_Subject_DocumentForm_Date_RevisionStatus.ext
Example: CPE_Records-Management_POL_2025-01-20_Rev0.pdf

BASIC FORMAT (minimal info):
Subject_DocumentForm_Date_RevisionStatus.ext
Example: Naming-Conventions_LPR_2025-03-11_RevA.docx

=== STEP 3: RESPOND WITH JSON (no markdown) ===
{{"suggestedName": "GeneratedFilename.pdf", "formatUsed": "course|advanced|basic", "extractedFields": {{"facultySchool": "FHSD-SoN or null", "courseCode": "0386-0001 or null", "term": "2024WT2 or null", "projectCode": "CPE or null", "subject": "Subject-In-Title-Kebab-Case", "documentForm": "CODE", "date": "YYYY-MM-DD", "revision": "Rev0"}}, "reasoning": "I found [text]. Faculty: [X]. School: [X]. Term: [X]. Document type: [X].", "confidence": 9}}"""

    elif content_type == "image":
        ext = file_name.split(".")[-1] if "." in file_name else "jpg"
        return f"""Analyze what is shown in this image and create a CPE-compliant filename.

Current filename: {file_name}

Key elements for the filename:
- Subject (required): What is actually shown in the image. Use Title-Kebab-Case (e.g., Campus-Building). MAX 50 CHARACTERS.
- Document Form: Use IMG for photos, SCR for screenshots, DIA for diagrams
- Date: Use today's date {today} if no date is visible
- Revision: Use 'Rev0' for final version

Respond with ONLY a JSON object:
{{"suggestedName": "Content-Description_IMG_{today}_Rev0.{ext}", "formatUsed": "basic", "extractedFields": {{"facultySchool": null, "courseCode": null, "term": null, "projectCode": null, "subject": "Subject-In-Title-Kebab-Case", "documentForm": "IMG", "date": "{today}", "revision": "Rev0"}}, "reasoning": "I can see [description]. I chose [Subject] because [reason]. I used IMG/SCR/DIA because [reason].", "confidence": 8}}"""

    else:
        return f"""Analyze this document and suggest a CPE-compliant filename.

Current file: {file_name}
Today's date: {today}

=== STEP 1: CHECK FOR FACULTY-SCHOOL (STRICT MATCHING ONLY) ===
ONLY use Faculty-School codes if you find EXACT matches to these UBC Okanagan names:
- "Irving K. Barber Faculty of Arts and Social Sciences" → IKBASS
- "Irving K. Barber Faculty of Science" → IKBFOS
- "Faculty of Creative and Critical Studies" → FCCS
- "Okanagan School of Education" → OSE
- "Faculty of Applied Science" + "School of Engineering" → APSC-SoE
- "Faculty of Health and Social Development" → FHSD
  - + "School of Nursing" → FHSD-SoN
  - + "School of Social Work" → FHSD-SSW
- "Faculty of Management" → FoM
- "Faculty of Medicine" → MED
- "College of Graduate Studies" → CoGS

DO NOT invent Faculty-School codes! If you don't see these EXACT faculty names, set facultySchool to null.

=== STEP 2: EXTRACT OTHER FIELDS ===
- COURSE CODE: Four digits + dash + four digits (e.g., 0386-0001). Must be this exact format.
- TERM: Format YYYYST (e.g., 2025WT1). Only if you see clear term/session info.
- PROJECT CODE: Only if explicitly labeled (e.g., "Project: CPE", "Account: XYZ")
- SUBJECT: Use Title-Kebab-Case (e.g., Foundations-For-Restorative-Approach)
  MAX 50 CHARACTERS for subject! Truncate at word boundary if longer.
- DOCUMENT FORM: Match keywords to codes:
  - Report/Enrollment/Count/Chart → RPT | Survey/Analysis → SRY | Summary → SUM
  - Letter of Proficiency → LPR | Letter of Completion → LCO
  - Guidelines/Guide → GUI | Manual → MNL | Template → TEM | Schedule → SCH
  - Budget → BGT | Invoice → INV | Contract → CON | Form → FRM
  - Agenda → AGD | Minutes → MIN | Policy → POL | Procedure → PRC
  - Presentation → PRS | Plan → PLN | Proposal → PRO
- REVISION: RevA/B/C for drafts, Rev0 for first final, Rev1/2 for subsequent

=== STEP 3: CHOOSE FORMAT ===
COURSE FORMAT (ONLY if you found valid Faculty-School AND course content):
Faculty-School_CourseCode_Term_DocumentForm_Date_Revision.ext

ADVANCED FORMAT (if project code is explicitly present):
ProjectCode_Subject_DocumentForm_Date_Revision.ext

BASIC FORMAT (default - use this for most files):
Subject_DocumentForm_Date_Revision.ext

=== STEP 4: RESPOND WITH JSON ===
Respond with ONLY this JSON (no markdown):
{{"suggestedName": "Filename.ext", "formatUsed": "course|advanced|basic", "extractedFields": {{"facultySchool": "CODE or null", "courseCode": "XXXX-XXXX or null", "term": "YYYYST or null", "projectCode": "CODE or null", "subject": "Subject-In-Title-Kebab-Case", "documentForm": "CODE", "date": "{today}", "revision": "Rev0"}}, "reasoning": "Explanation of what I found and why I chose each field.", "confidence": 8}}"""


def _parse_ai_response(response_text: str, file_name: str, today: str) -> dict:
    """Parse JSON from AI response text, with fallback."""
    try:
        cleaned = re.sub(r"```json\s*", "", response_text)
        cleaned = re.sub(r"```\s*", "", cleaned)
        cleaned = cleaned.strip()

        json_match = re.search(r"\{[\s\S]*\}", cleaned)
        if json_match:
            result = json.loads(json_match.group())
            return {"success": True, "analysis": result}
    except json.JSONDecodeError:
        pass

    ext = file_name.split(".")[-1] if "." in file_name else "pdf"
    return {
        "success": True,
        "analysis": {
            "suggestedName": f"Document_{today}_Rev0.{ext}",
            "formatUsed": "basic",
            "extractedFields": {},
            "reasoning": "AI analysis completed but response format was unclear.",
            "confidence": 3,
        },
    }


def analyze_with_claude(
    api_key: str, content: str, file_name: str, content_type: str, privacy_level: str
) -> dict:
    """Analyze file content with Claude API."""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        today = datetime.now().strftime("%Y-%m-%d")
        is_pdf = file_name.lower().endswith(".pdf")
        prompt = _build_analysis_prompt(file_name, today, content_type, is_pdf)

        if content_type == "image":
            mime_type = content.split(";")[0].replace("data:", "")
            base64_data = content.split(",")[1]

            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1000,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": base64_data,
                                },
                            },
                        ],
                    }
                ],
            )
        else:
            document_content = content[:MAX_EXCEL_CONTENT]
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1000,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": prompt + f"\n\nContent: {document_content}",
                    }
                ],
            )

        return _parse_ai_response(message.content[0].text, file_name, today)

    except Exception as e:
        error_msg = str(e)
        if "AuthenticationError" in type(e).__name__:
            return {"success": False, "error": "Invalid API key. Please check your Claude API key."}
        if "RateLimitError" in type(e).__name__:
            return {"success": False, "error": "Rate limit exceeded. Please wait a moment and try again."}
        return {"success": False, "error": error_msg[:200]}


def analyze_with_gemini(
    api_key: str, content: str, file_name: str, content_type: str, privacy_level: str
) -> dict:
    """Analyze file content with Gemini via OpenRouter API."""
    try:
        import requests

        today = datetime.now().strftime("%Y-%m-%d")
        is_pdf = file_name.lower().endswith(".pdf")
        prompt = _build_analysis_prompt(file_name, today, content_type, is_pdf)

        if content_type == "image":
            mime_type = content.split(";")[0].replace("data:", "")
            base64_data = content.split(",")[1]

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{base64_data}"},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
        else:
            document_content = content[:MAX_TEXT_CONTENT]
            messages = [
                {
                    "role": "user",
                    "content": f"{SYSTEM_PROMPT}\n\n{prompt}\n\nContent: {document_content}",
                }
            ]

        payload = json.dumps({"model": GEMINI_MODEL, "messages": messages}, ensure_ascii=False)
        response = requests.post(
            OPENROUTER_BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ubc-cpe-naming-tool.streamlit.app",
                "X-Title": "UBC CPE File Naming Tool",
            },
            data=payload.encode("utf-8"),
            timeout=60,
        )

        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return {"success": False, "error": f"API error: {error_msg}"}

        result_data = response.json()
        response_text = result_data["choices"][0]["message"]["content"]
        return _parse_ai_response(response_text, file_name, today)

    except Exception as e:
        error_msg = str(e)
        if "Timeout" in type(e).__name__:
            return {"success": False, "error": "Request timed out. Please try again."}
        if "429" in error_msg:
            return {"success": False, "error": "Rate limit reached. Please wait a moment and try again."}
        return {"success": False, "error": f"Error: {error_msg[:200]}"}


# ─── Rule-based fallback analyzer ──────────────────────────────────────────


def analyze_with_rules(content: str, file_name: str, content_type: str) -> dict:
    """Rule-based fallback analyzer when AI APIs are unavailable.

    Extracts information using pattern matching on the text content.
    Works offline with no API key required.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    ext = file_name.split(".")[-1] if "." in file_name else "pdf"

    # For images, we can only use the filename
    if content_type == "image":
        text = file_name
    else:
        text = content

    text_lower = text.lower()

    # Extract fields using pattern matching
    extracted = {
        "facultySchool": None,
        "courseCode": None,
        "term": None,
        "projectCode": None,
        "subject": None,
        "documentForm": None,
        "date": today,
        "revision": "Rev0",
    }
    reasoning_parts = []

    # 1. Faculty-School detection
    for pattern, code in FACULTY_PATTERNS.items():
        if pattern.lower() in text_lower:
            extracted["facultySchool"] = code
            reasoning_parts.append(f"Found faculty reference: {pattern} -> {code}")
            break

    # 2. Course code detection (####-####)
    course_match = re.search(r"\b(\d{4}-\d{4})\b", text)
    if course_match:
        extracted["courseCode"] = course_match.group(1)
        reasoning_parts.append(f"Found course code: {course_match.group(1)}")

    # 3. Term detection (YYYYWT1/ST1 pattern)
    term_match = re.search(r"\b(20\d{2}[WS]T[12])\b", text)
    if term_match:
        extracted["term"] = term_match.group(1)
        reasoning_parts.append(f"Found term: {term_match.group(1)}")

    # 4. Date detection
    date_patterns = [
        (r"\b(\d{4}-\d{2}-\d{2})\b", "%Y-%m-%d"),
        (r"\b(\d{2}/\d{2}/\d{4})\b", "%m/%d/%Y"),
        (r"\b(\w+ \d{1,2},? \d{4})\b", None),
    ]
    for pattern, fmt in date_patterns:
        date_match = re.search(pattern, text)
        if date_match:
            try:
                if fmt:
                    parsed = datetime.strptime(date_match.group(1), fmt)
                    extracted["date"] = parsed.strftime("%Y-%m-%d")
                    reasoning_parts.append(f"Found date: {date_match.group(1)}")
                    break
            except ValueError:
                continue

    # 5. Document form detection
    for keyword, code in sorted(DOCUMENT_FORM_KEYWORDS.items(), key=lambda x: -len(x[0])):
        if keyword in text_lower:
            extracted["documentForm"] = code
            reasoning_parts.append(f"Detected document type: '{keyword}' -> {code}")
            break

    # 6. Subject extraction from filename
    base_name = file_name.rsplit(".", 1)[0] if "." in file_name else file_name
    # Clean up filename to extract subject
    subject = re.sub(r"[_\s]+", "-", base_name)
    subject = re.sub(r"[^A-Za-z0-9\-]", "", subject)
    # Title case
    parts = subject.split("-")
    subject = "-".join(p.capitalize() for p in parts if p)
    if len(subject) > 50:
        # Truncate at word boundary
        subject = subject[:50].rsplit("-", 1)[0]
    extracted["subject"] = subject or "Document"
    reasoning_parts.append(f"Derived subject from filename: {extracted['subject']}")

    # Determine format
    if extracted["facultySchool"] and extracted["courseCode"]:
        format_used = "course"
    elif extracted.get("projectCode"):
        format_used = "advanced"
    else:
        format_used = "basic"

    # Build filename
    elements = []
    if format_used == "course":
        if extracted["facultySchool"]:
            elements.append(extracted["facultySchool"])
        if extracted["courseCode"]:
            elements.append(extracted["courseCode"])
        if extracted["term"]:
            elements.append(extracted["term"])
    elements.append(extracted["subject"])
    if extracted["documentForm"]:
        elements.append(extracted["documentForm"])
    elements.append(extracted["date"])
    elements.append(extracted["revision"])

    suggested_name = "_".join(elements) + "." + ext

    reasoning = "Rule-based analysis (offline mode). " + ". ".join(reasoning_parts) if reasoning_parts else "Rule-based analysis from filename only."

    return {
        "success": True,
        "analysis": {
            "suggestedName": suggested_name,
            "formatUsed": format_used,
            "extractedFields": extracted,
            "reasoning": reasoning,
            "confidence": 4,  # Lower confidence for rule-based
        },
    }


# ─── Confidence classification ─────────────────────────────────────────────


def get_confidence_level(confidence: int) -> dict:
    """Classify confidence score into level with color and message.

    Returns dict with 'level', 'color', 'icon', and 'message'.
    """
    if confidence >= 8:
        return {
            "level": "high",
            "color": "green",
            "icon": "✅",
            "message": "High confidence - AI is very sure about this suggestion.",
        }
    elif confidence >= 5:
        return {
            "level": "medium",
            "color": "orange",
            "icon": "⚠️",
            "message": "Medium confidence - Review the suggestion before using.",
        }
    else:
        return {
            "level": "low",
            "color": "red",
            "icon": "🔴",
            "message": "Low confidence - Manual review strongly recommended.",
        }
