import re
from typing import Any

QUALIFICATIONS = ["MBBS", "BDS", "BSc Nursing", "MD", "MS", "DM", "MCh", "DNB", "Fellowship"]
SPECIALIZATIONS = [
    "Internal Medicine",
    "General Medicine",
    "Cardiology",
    "Neurology",
    "Oncology",
    "Pediatrics",
    "Orthopedics",
    "Radiology",
    "Anesthesiology",
    "Dermatology",
    "Gynecology",
    "Emergency Medicine",
    "Nursing",
]


def fallback_extract(text: str) -> dict[str, Any]:
    email = _first(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone = _clean_phone(_first(r"(?:\+91[-\s]?)?[6-9][\d\s-]{9,14}", text))
    qualifications = [q for q in QUALIFICATIONS if re.search(rf"\b{re.escape(q)}\b", text, re.IGNORECASE)]
    specialization = next((s for s in SPECIALIZATIONS if re.search(rf"\b{re.escape(s)}\b", text, re.IGNORECASE)), None)
    exp_match = _experience_match(text)
    nmc = _first(r"\bNMC(?:\s*Registration)?(?:\s*No\.?)?\s*[:#-]?\s*([A-Z0-9/-]{4,})", text)
    skills = _section_items(text, "Skills", ("Certifications", "Languages", "Publications", "Education"))
    certifications = _section_items(text, "Certifications", ("Languages", "Publications", "Education", "Work Experience", "Professional Experience"))
    publications_count = 1 if re.search(r"\bpublications?\b|\bresearch papers?\b", text, re.IGNORECASE) else None

    return {
        "name": _guess_name(text),
        "email": email,
        "phone": phone,
        "qualification": qualifications,
        "specialization": specialization,
        "experience_years": float(exp_match.group(1)) if exp_match else None,
        "nmc_registration": nmc,
        "clinical_skills": skills,
        "medical_certifications": certifications,
        "publications_count": publications_count,
    }


def _first(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    return match.group(1) if match.lastindex else match.group(0)


def _guess_name(text: str) -> str | None:
    for line in text.splitlines()[:8]:
        candidate = line.strip()
        if 3 <= len(candidate) <= 80 and not re.search(r"@|\d{6,}", candidate):
            return candidate
    return None


def _clean_phone(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"\s+", " ", value).strip()


def _experience_match(text: str):
    patterns = [
        r"(?:over|more than|around|approximately)?\s*(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s+of\s+(?:clinical\s+)?experience",
        r"(?:professional\s+)?experience\s*\(?\s*(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s*\)?",
        r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s+(?:of\s+)?(?:clinical\s+)?experience",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match
    return None


def _section_items(text: str, heading: str, stop_headings: tuple[str, ...]) -> list[str]:
    stop_pattern = "|".join(re.escape(item) for item in stop_headings)
    match = re.search(
        rf"{re.escape(heading)}\s*\n(?P<body>.*?)(?:\n(?:{stop_pattern})\b|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return []
    body = match.group("body")
    parts = re.split(r",|•|\n", body)
    return [part.strip(" .;-") for part in parts if 2 < len(part.strip(" .;-")) <= 80][:12]
