import re
from typing import Any

QUALIFICATIONS = ["MBBS", "BDS", "BSc Nursing", "MD", "MS", "DM", "MCh", "DNB", "Fellowship"]
SPECIALIZATIONS = [
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
    phone = _first(r"(?:\+91[-\s]?)?[6-9]\d{9}", text)
    qualifications = [q for q in QUALIFICATIONS if re.search(rf"\b{re.escape(q)}\b", text, re.IGNORECASE)]
    specialization = next((s for s in SPECIALIZATIONS if re.search(rf"\b{re.escape(s)}\b", text, re.IGNORECASE)), None)
    exp_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s+(?:of\s+)?experience", text, re.IGNORECASE)
    nmc = _first(r"\bNMC(?:\s*Registration)?(?:\s*No\.?)?\s*[:#-]?\s*([A-Z0-9/-]{4,})", text)

    return {
        "name": _guess_name(text),
        "email": email,
        "phone": phone,
        "qualification": qualifications,
        "specialization": specialization,
        "experience_years": float(exp_match.group(1)) if exp_match else None,
        "nmc_registration": nmc,
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
