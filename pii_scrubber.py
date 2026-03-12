"""
PII (Personally Identifiable Information) scrubber for the UBC CPE File Naming Tool.

Uses Microsoft Presidio to detect and redact personal information from document
text before sending it to AI providers for analysis. This ensures that names,
emails, phone numbers, social insurance numbers, and other sensitive data
never leave the local environment.

Supported PII types:
- Person names (first, last, full)
- Email addresses
- Phone numbers
- Social Insurance Numbers (Canadian SIN)
- Credit card numbers
- IP addresses
- US/CA Social Security / Insurance numbers
- Dates of birth
- Physical addresses / locations
- Custom patterns (student IDs, employee IDs)
"""

import re
from typing import Optional

# Presidio availability flag
try:
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False


# ─── Custom recognizers for Canadian / UBC-specific PII ────────────────────

def _build_custom_recognizers() -> list:
    """Build custom pattern recognizers for Canadian PII and UBC-specific IDs."""
    recognizers = []

    # Canadian Social Insurance Number (SIN): ###-###-### or #########
    sin_pattern = Pattern(
        name="canadian_sin",
        regex=r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b",
        score=0.7,
    )
    sin_recognizer = PatternRecognizer(
        supported_entity="CA_SIN",
        name="Canadian SIN Recognizer",
        patterns=[sin_pattern],
        context=["sin", "social insurance", "social insurance number"],
    )
    recognizers.append(sin_recognizer)

    # UBC Student ID: typically 8 digits
    student_id_pattern = Pattern(
        name="ubc_student_id",
        regex=r"\b\d{8}\b",
        score=0.3,  # Low base score, boosted by context
    )
    student_id_recognizer = PatternRecognizer(
        supported_entity="STUDENT_ID",
        name="UBC Student ID Recognizer",
        patterns=[student_id_pattern],
        context=["student id", "student number", "student #", "learner id"],
    )
    recognizers.append(student_id_recognizer)

    # Employee ID patterns
    employee_id_pattern = Pattern(
        name="employee_id",
        regex=r"\b[Ee]mp[-#]?\d{4,8}\b",
        score=0.6,
    )
    employee_id_recognizer = PatternRecognizer(
        supported_entity="EMPLOYEE_ID",
        name="Employee ID Recognizer",
        patterns=[employee_id_pattern],
        context=["employee", "staff", "emp id", "employee number"],
    )
    recognizers.append(employee_id_recognizer)

    return recognizers


# ─── Singleton engine setup ────────────────────────────────────────────────

_analyzer_engine: Optional["AnalyzerEngine"] = None
_anonymizer_engine: Optional["AnonymizerEngine"] = None


def _get_engines():
    """Lazily initialize Presidio engines (expensive, so only do once)."""
    global _analyzer_engine, _anonymizer_engine

    if not PRESIDIO_AVAILABLE:
        return None, None

    if _analyzer_engine is None:
        try:
            _analyzer_engine = AnalyzerEngine()
            # Register custom recognizers
            for recognizer in _build_custom_recognizers():
                _analyzer_engine.registry.add_recognizer(recognizer)
        except Exception:
            # spaCy model not installed — fall back to regex
            return None, None

    if _anonymizer_engine is None:
        _anonymizer_engine = AnonymizerEngine()

    return _analyzer_engine, _anonymizer_engine


# ─── PII entity types to detect ───────────────────────────────────────────

# Default entities to scan for
DEFAULT_PII_ENTITIES = [
    "PERSON",           # Names
    "EMAIL_ADDRESS",    # Email addresses
    "PHONE_NUMBER",     # Phone numbers
    "CA_SIN",           # Canadian Social Insurance Number (custom)
    "CREDIT_CARD",      # Credit card numbers
    "US_SSN",           # US Social Security Number
    "IP_ADDRESS",       # IP addresses
    "STUDENT_ID",       # UBC Student ID (custom)
    "EMPLOYEE_ID",      # Employee ID (custom)
    "LOCATION",         # Physical addresses
    "DATE_TIME",        # Dates that might be birthdates
    "US_PASSPORT",      # Passport numbers
    "US_DRIVER_LICENSE", # Driver license
]

# Minimum confidence score for detection
DEFAULT_SCORE_THRESHOLD = 0.5


def scrub_text(
    text: str,
    entities: list[str] | None = None,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    replacement_format: str = "<{entity_type}>",
) -> tuple[str, list[dict]]:
    """Scrub PII from text using Microsoft Presidio.

    Args:
        text: The input text to scrub
        entities: List of entity types to detect (None = all defaults)
        score_threshold: Minimum confidence score for detection (0-1)
        replacement_format: Format string for replacements, uses {entity_type}

    Returns:
        Tuple of (scrubbed_text, detected_entities_list)
        Each detected entity is a dict with: type, start, end, score, original_text
    """
    if not PRESIDIO_AVAILABLE:
        return _fallback_scrub(text)

    analyzer, anonymizer = _get_engines()
    if analyzer is None:
        return _fallback_scrub(text)

    if entities is None:
        entities = DEFAULT_PII_ENTITIES

    # Analyze text for PII
    results = analyzer.analyze(
        text=text,
        entities=entities,
        language="en",
        score_threshold=score_threshold,
    )

    if not results:
        return text, []

    # Build detected entities list
    detected = []
    for result in results:
        detected.append({
            "type": result.entity_type,
            "start": result.start,
            "end": result.end,
            "score": round(result.score, 2),
            "original_text": text[result.start:result.end],
        })

    # Anonymize the text
    operators = {}
    for entity_type in set(r.entity_type for r in results):
        placeholder = replacement_format.format(entity_type=entity_type)
        operators[entity_type] = OperatorConfig("replace", {"new_value": placeholder})

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=operators,
    )

    return anonymized.text, detected


def _fallback_scrub(text: str) -> tuple[str, list[dict]]:
    """Regex-based PII scrubbing fallback when Presidio is not available."""
    detected = []
    scrubbed = text

    # Email addresses
    for match in re.finditer(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", scrubbed):
        detected.append({
            "type": "EMAIL_ADDRESS",
            "start": match.start(),
            "end": match.end(),
            "score": 0.95,
            "original_text": match.group(),
        })
    scrubbed = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "<EMAIL_ADDRESS>",
        scrubbed,
    )

    # Phone numbers (various formats)
    for match in re.finditer(
        r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", scrubbed
    ):
        detected.append({
            "type": "PHONE_NUMBER",
            "start": match.start(),
            "end": match.end(),
            "score": 0.8,
            "original_text": match.group(),
        })
    scrubbed = re.sub(
        r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "<PHONE_NUMBER>",
        scrubbed,
    )

    # Canadian SIN: ###-###-###
    for match in re.finditer(r"\b\d{3}[-\s]\d{3}[-\s]\d{3}\b", scrubbed):
        detected.append({
            "type": "CA_SIN",
            "start": match.start(),
            "end": match.end(),
            "score": 0.7,
            "original_text": match.group(),
        })
    scrubbed = re.sub(r"\b\d{3}[-\s]\d{3}[-\s]\d{3}\b", "<CA_SIN>", scrubbed)

    # Credit card numbers (basic pattern)
    for match in re.finditer(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", scrubbed):
        detected.append({
            "type": "CREDIT_CARD",
            "start": match.start(),
            "end": match.end(),
            "score": 0.8,
            "original_text": match.group(),
        })
    scrubbed = re.sub(
        r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        "<CREDIT_CARD>",
        scrubbed,
    )

    # IP addresses
    for match in re.finditer(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b", scrubbed
    ):
        detected.append({
            "type": "IP_ADDRESS",
            "start": match.start(),
            "end": match.end(),
            "score": 0.8,
            "original_text": match.group(),
        })
    scrubbed = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "<IP_ADDRESS>", scrubbed)

    return scrubbed, detected


def get_pii_summary(detected: list[dict]) -> dict:
    """Summarize detected PII by type.

    Returns dict mapping entity type to count.
    """
    summary = {}
    for entity in detected:
        entity_type = entity["type"]
        summary[entity_type] = summary.get(entity_type, 0) + 1
    return summary


def is_available() -> bool:
    """Check if Presidio and its spaCy model are available for full PII detection."""
    if not PRESIDIO_AVAILABLE:
        return False
    try:
        import spacy
        spacy.load("en_core_web_sm")
        return True
    except Exception:
        return False


# Friendly names for PII entity types (for UI display)
PII_ENTITY_LABELS = {
    "PERSON": "Person Names",
    "EMAIL_ADDRESS": "Email Addresses",
    "PHONE_NUMBER": "Phone Numbers",
    "CA_SIN": "Social Insurance Numbers (SIN)",
    "CREDIT_CARD": "Credit Card Numbers",
    "US_SSN": "Social Security Numbers",
    "IP_ADDRESS": "IP Addresses",
    "STUDENT_ID": "Student IDs",
    "EMPLOYEE_ID": "Employee IDs",
    "LOCATION": "Physical Addresses",
    "DATE_TIME": "Dates (potential DOB)",
    "US_PASSPORT": "Passport Numbers",
    "US_DRIVER_LICENSE": "Driver License Numbers",
}
