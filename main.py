"""
FastAPI backend for the UBC CPE File Naming Tool.

Serves both API endpoints and static frontend files. Replaces the Streamlit
app.py as the application entrypoint.
"""

import os
import io
import csv
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from constants import (
    DOCUMENT_FORMS,
    REVISION_STATUSES,
    FILE_EXTENSIONS,
    PARTNERS,
    CPE_INTERNAL_BLOCKS,
    CPE_INTERNAL_SUBCATEGORIES,
    DEFINITION_APPROVALS_BLOCKS,
    PRODUCTION_DELIVERY_BLOCKS,
    HELP_CONTENT,
    FILE_LOCATION_HELP,
    SUPPORTED_FILE_TYPES,
)
from filename_generator import generate_filename, validate_all_fields, check_filename_length
from file_location import generate_file_location_path
from file_processing import read_file_content, compute_file_hash
from ai_analysis import (
    analyze_with_claude,
    analyze_with_gemini,
    analyze_with_rules,
    get_confidence_level,
)
from pii_scrubber import scrub_text, get_pii_summary, is_available as pii_is_available, PII_ENTITY_LABELS

app = FastAPI(title="UBC CPE File Naming Tool")

# ─── Auth config ──────────────────────────────────────────────────────────

APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "cpe-naming-tool-secret-key-change-me")
TOKEN_MAX_AGE = 86400  # 24 hours

serializer = URLSafeTimedSerializer(SECRET_KEY)


def create_token() -> str:
    return serializer.dumps({"authenticated": True})


def verify_token(token: str) -> bool:
    try:
        data = serializer.loads(token, max_age=TOKEN_MAX_AGE)
        return data.get("authenticated", False)
    except (BadSignature, SignatureExpired):
        return False


async def require_auth(request: Request):
    """Dependency that enforces authentication when APP_PASSWORD is set."""
    if not APP_PASSWORD:
        return True
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth_header[7:]
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return True


# ─── File adapter ─────────────────────────────────────────────────────────

class FileAdapter:
    """Adapter to make FastAPI's UploadFile work with existing file processing functions."""

    def __init__(self, upload_file: UploadFile, content: bytes):
        self.name = upload_file.filename or "unknown"
        self._content = content
        self._pos = 0

    def read(self) -> bytes:
        data = self._content[self._pos:]
        self._pos = len(self._content)
        return data

    def seek(self, pos: int):
        self._pos = pos


# ─── In-memory cache ──────────────────────────────────────────────────────

_ai_cache: dict[str, dict] = {}

# ─── API Routes ───────────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    return {"status": "ok", "auth_required": bool(APP_PASSWORD)}


@app.post("/api/auth/login")
async def login(request: Request):
    body = await request.json()
    password = body.get("password", "")

    if not APP_PASSWORD:
        return {"token": create_token(), "auth_required": False}

    if password == APP_PASSWORD:
        return {"token": create_token(), "auth_required": True}

    raise HTTPException(status_code=401, detail="Invalid password")


@app.get("/api/config", dependencies=[Depends(require_auth)])
async def get_config():
    return {
        "document_forms": DOCUMENT_FORMS,
        "revision_statuses": REVISION_STATUSES,
        "file_extensions": FILE_EXTENSIONS,
        "partners": PARTNERS,
        "cpe_internal_blocks": CPE_INTERNAL_BLOCKS,
        "cpe_internal_subcategories": CPE_INTERNAL_SUBCATEGORIES,
        "definition_approvals_blocks": DEFINITION_APPROVALS_BLOCKS,
        "production_delivery_blocks": PRODUCTION_DELIVERY_BLOCKS,
        "help_content": HELP_CONTENT,
        "file_location_help": FILE_LOCATION_HELP,
        "supported_file_types": SUPPORTED_FILE_TYPES,
        "pii_entity_labels": PII_ENTITY_LABELS,
        "pii_available": pii_is_available(),
        "auth_required": bool(APP_PASSWORD),
    }


@app.post("/api/generate-filename", dependencies=[Depends(require_auth)])
async def api_generate_filename(request: Request):
    body = await request.json()
    format_type = body.get("format_type", "basic")
    subject = body.get("subject", "")
    date_str = body.get("date", "")
    revision = body.get("revision", "A")
    extension = body.get("extension", "pdf")
    project_code = body.get("project_code", "")
    document_form = body.get("document_form", "")
    faculty_school = body.get("faculty_school", "")
    course_code = body.get("course_code", "")
    term = body.get("term", "")

    # Validate
    errors = validate_all_fields(
        format_type, subject, project_code, document_form,
        faculty_school, course_code, term,
    )
    if errors:
        return JSONResponse(
            status_code=422,
            content={
                "errors": [
                    {"message": e.message, "level": e.level} for e in errors
                ]
            },
        )

    # Parse date
    try:
        date_val = datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return JSONResponse(
            status_code=422,
            content={"errors": [{"message": "Invalid date format. Use YYYY-MM-DD.", "level": "error"}]},
        )

    standard_name, sharepoint_name = generate_filename(
        format_type, subject, date_val, revision, extension,
        project_code, document_form, faculty_school, course_code, term,
    )

    length_check = check_filename_length(standard_name)

    return {
        "standard_name": standard_name,
        "sharepoint_name": sharepoint_name,
        "length_check": {
            "valid": length_check.valid,
            "message": length_check.message,
            "level": length_check.level,
        },
    }


@app.post("/api/file-location", dependencies=[Depends(require_auth)])
async def api_file_location(request: Request):
    body = await request.json()
    breadcrumb_path, folder_path = generate_file_location_path(
        is_partner_related=body.get("is_partner_related", False),
        cpe_block=body.get("cpe_block", ""),
        cpe_subcat=body.get("cpe_subcat", ""),
        partner=body.get("partner", ""),
        phase=body.get("phase", ""),
        subject_area=body.get("subject_area", ""),
        credential=body.get("credential", ""),
        applies_to_all=body.get("applies_to_all", True),
        occurrence=body.get("occurrence", ""),
        file_type=body.get("file_type", ""),
    )
    return {"breadcrumb_path": breadcrumb_path, "folder_path": folder_path}


@app.post("/api/scan-pii", dependencies=[Depends(require_auth)])
async def api_scan_pii(file: UploadFile = File(...)):
    content_bytes = await file.read()
    adapter = FileAdapter(file, content_bytes)

    content, content_type = read_file_content(adapter)

    if content_type == "text" and isinstance(content, str):
        scrubbed, detected = scrub_text(content)
        summary = get_pii_summary(detected)
        return {
            "filename": file.filename,
            "pii_items": detected,
            "pii_summary": summary,
        }

    return {"filename": file.filename, "pii_items": [], "pii_summary": {}}


@app.post("/api/analyze", dependencies=[Depends(require_auth)])
async def api_analyze(
    file: UploadFile = File(...),
    provider: str = Form("offline"),
    api_key: str = Form(""),
):
    content_bytes = await file.read()
    adapter = FileAdapter(file, content_bytes)

    # Check cache
    file_hash = compute_file_hash(adapter)
    cache_key = f"{provider}:{file_hash}"

    if cache_key in _ai_cache:
        cached = _ai_cache[cache_key].copy()
        cached["file"] = file.filename
        cached["cached"] = True
        return cached

    # Read content
    adapter.seek(0)
    content, content_type = read_file_content(adapter)

    if content_type == "unknown":
        return {"file": file.filename, "success": False, "error": "Unsupported file type"}

    # PII scrubbing on text content
    pii_detected = []
    if content_type == "text" and isinstance(content, str):
        content, pii_detected = scrub_text(content)

    # Resolve API key from env if not provided
    if not api_key:
        if provider == "gemini":
            api_key = os.environ.get("OPENROUTER_API_KEY", "")
        elif provider == "claude":
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    # Analyze
    if provider == "gemini":
        result = analyze_with_gemini(api_key, content, file.filename, content_type, "standard")
    elif provider == "claude":
        result = analyze_with_claude(api_key, content, file.filename, content_type, "standard")
    else:
        result = analyze_with_rules(content, file.filename, content_type)

    result["file"] = file.filename
    result["cached"] = False
    result["pii_detected"] = pii_detected

    # Add confidence level
    if result.get("success") and result.get("analysis"):
        confidence = result["analysis"].get("confidence", 5)
        result["confidence_level"] = get_confidence_level(confidence)

    # Cache successful results
    if result.get("success"):
        _ai_cache[cache_key] = result

    return result


@app.post("/api/export-csv", dependencies=[Depends(require_auth)])
async def api_export_csv(request: Request):
    results = await request.json()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Original Filename", "Suggested Filename", "Format Used",
        "Faculty-School", "Course Code", "Term", "Project Code",
        "Subject", "Document Form", "Date", "Revision",
        "Confidence", "AI Reasoning",
    ])

    for result in results:
        if result.get("success"):
            analysis = result.get("analysis", {})
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
                "ERROR", "", "", "", "", "", "", "", "", "", "",
                result.get("error", ""),
            ])

    csv_content = output.getvalue()
    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cpe_analysis_results.csv"},
    )


# ─── Static files & SPA fallback ─────────────────────────────────────────

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_index():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())
