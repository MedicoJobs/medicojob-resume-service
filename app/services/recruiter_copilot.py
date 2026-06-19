from __future__ import annotations

import re
from collections import Counter

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ResumeRecord
from app.models.copilot import (
    CandidateComparison,
    CandidateMatch,
    CandidateProfileResponse,
    RecruiterCopilotResponse,
    RecruiterSearchIntent,
)
from app.services.candidate_decisions import latest_candidate_decision
from app.services.local_resume_store import load_local_resume_records

SPECIALIZATIONS = [
    "cardiology",
    "neurology",
    "orthopedics",
    "oncology",
    "pediatrics",
    "paediatrics",
    "dermatology",
    "radiology",
    "anesthesiology",
    "anaesthesiology",
    "gynecology",
    "gynaecology",
    "urology",
    "nephrology",
    "psychiatry",
    "emergency medicine",
    "general medicine",
    "nursing",
]

SPECIALIZATION_ALIASES = {
    "cardiologist": "Cardiology",
    "cardiologists": "Cardiology",
    "neurologist": "Neurology",
    "neurologists": "Neurology",
    "orthopedic": "Orthopedics",
    "orthopedist": "Orthopedics",
    "paediatrician": "Pediatrics",
    "pediatrician": "Pediatrics",
    "dermatologist": "Dermatology",
    "radiologist": "Radiology",
    "anesthetist": "Anesthesiology",
    "anaesthetist": "Anesthesiology",
    "gynecologist": "Gynecology",
    "gynaecologist": "Gynecology",
    "urologist": "Urology",
    "nephrologist": "Nephrology",
    "psychiatrist": "Psychiatry",
    "nurse": "Nursing",
    "nurses": "Nursing",
}


async def run_recruiter_copilot(db: AsyncSession, query: str, limit: int) -> RecruiterCopilotResponse:
    intent = parse_recruiter_query(query)
    query_terms = _query_terms(query)
    try:
        result = await db.execute(select(ResumeRecord).order_by(ResumeRecord.created_at.desc()).limit(500))
        records = list(result.scalars().all())
    except (ConnectionError, OSError, SQLAlchemyError):
        records = load_local_resume_records(limit=500)
        if not records:
            return _empty_response(
                query=query,
                intent=intent,
                message="Candidate resume database is unavailable. Upload a resume again so the local candidate store can be created.",
            )

    ranked = sorted(
        (_build_candidate_match(record, intent, query, query_terms) for record in records),
        key=lambda candidate: candidate.match_score,
        reverse=True,
    )
    minimum_score = 25 if query_terms and not intent.specialization and intent.min_experience_years is None else 35
    matches = [candidate for candidate in ranked if candidate.match_score >= minimum_score]
    top_candidates = matches[:limit]

    return RecruiterCopilotResponse(
        query=query,
        intent=intent,
        total_candidates=len(matches),
        returned_candidates=len(top_candidates),
        best_match_score=top_candidates[0].match_score if top_candidates else 0,
        top_candidates=top_candidates,
        comparison=[_compare_candidate(candidate) for candidate in top_candidates],
        shortlist_suggestions=_shortlist_suggestions(top_candidates),
        hiring_insights=_hiring_insights(matches, intent),
    )


async def get_candidate_profile(db: AsyncSession, candidate_id: int, hospital_id: str | None) -> CandidateProfileResponse | None:
    record = None
    try:
        result = await db.execute(select(ResumeRecord).where(ResumeRecord.id == candidate_id))
        record = result.scalar_one_or_none()
    except (ConnectionError, OSError, SQLAlchemyError):
        record = None

    if record is None:
        record = next((item for item in load_local_resume_records(limit=100000) if item.id == candidate_id), None)

    if record is None:
        return None

    return CandidateProfileResponse(
        id=record.id,
        user_id=getattr(record, "user_id", None),
        filename=getattr(record, "filename", None),
        analysis=getattr(record, "analysis", {}) or {},
        extracted_text_preview=(getattr(record, "extracted_text", "") or "")[:2500],
        decision=latest_candidate_decision(candidate_id, hospital_id),
    )


def _empty_response(query: str, intent: RecruiterSearchIntent, message: str) -> RecruiterCopilotResponse:
    return RecruiterCopilotResponse(
        query=query,
        intent=intent,
        total_candidates=0,
        returned_candidates=0,
        best_match_score=0,
        top_candidates=[],
        comparison=[],
        shortlist_suggestions=["No candidates are available for shortlisting yet."],
        hiring_insights=[message],
    )


def parse_recruiter_query(query: str) -> RecruiterSearchIntent:
    text = query.lower()
    min_experience = None
    experience_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", text)
    if experience_match:
        min_experience = float(experience_match.group(1))

    specialization = next((label for alias, label in SPECIALIZATION_ALIASES.items() if alias in text), None)
    if specialization is None:
        specialization = next((item.title() for item in SPECIALIZATIONS if item in text), None)
    if specialization == "Paediatrics":
        specialization = "Pediatrics"
    if specialization == "Anaesthesiology":
        specialization = "Anesthesiology"
    if specialization == "Gynaecology":
        specialization = "Gynecology"

    seniority = None
    for level in ("expert", "senior", "mid-level", "junior", "fresher"):
        if level in text:
            seniority = level.title()
            break

    skills = []
    for marker in ("with ", "skilled in ", "experience in "):
        if marker in text:
            tail = text.split(marker, 1)[1]
            skills = [part.strip(" .") for part in re.split(r",| and ", tail) if len(part.strip()) > 2][:5]
            skills = [skill for skill in skills if not re.search(r"\d+\s*\+?\s*(?:years?|yrs?)", skill)]
            break

    return RecruiterSearchIntent(
        specialization=specialization,
        min_experience_years=min_experience,
        skills=skills,
        seniority_level=seniority,
    )


def _build_candidate_match(record: ResumeRecord, intent: RecruiterSearchIntent, query: str, query_terms: list[str] | None = None) -> CandidateMatch:
    analysis = record.analysis or {}
    reasons = []
    score = 15
    searchable_text = _candidate_search_text(record, analysis)

    specialization = analysis.get("specialization")
    if intent.specialization:
        if _contains(specialization, intent.specialization) or _contains(query, specialization):
            score += 30
            reasons.append(f"Specialization matches {intent.specialization}.")
        else:
            score -= 15

    years = _number_or_none(analysis.get("experience_years"))
    if intent.min_experience_years is not None:
        if years is not None and years >= intent.min_experience_years:
            score += 25
            reasons.append(f"Has {years:g}+ years of experience.")
        else:
            score -= 20
            reasons.append("Experience is below the requested threshold or missing.")

    candidate_skills = [*_list(analysis.get("clinical_skills")), *_list(analysis.get("technical_skills"))]
    for skill in intent.skills:
        if any(_contains(candidate_skill, skill) for candidate_skill in candidate_skills):
            score += 6
            reasons.append(f"Skill match: {skill}.")

    keyword_hits = [term for term in (query_terms or []) if term in searchable_text]
    if keyword_hits:
        score += min(len(keyword_hits) * 12, 36)
        reasons.append(f"Keyword match: {', '.join(keyword_hits[:3])}.")
    elif query_terms and not intent.specialization and intent.min_experience_years is None:
        score -= 15

    resume_score = int(analysis.get("resume_score") or 0)
    score += min(resume_score // 5, 20)
    if resume_score >= 80:
        reasons.append("Strong resume intelligence score.")

    if analysis.get("nmc_registration") or analysis.get("state_medical_council_registration") or analysis.get("nursing_council_registration"):
        score += 5
        reasons.append("Registration details are available.")

    match_score = max(0, min(100, score))
    return CandidateMatch(
        id=record.id,
        name=analysis.get("name") or f"Candidate #{record.id}",
        specialization=specialization,
        experience_years=years,
        location=analysis.get("location"),
        current_employer=analysis.get("current_employer"),
        qualification=_list(analysis.get("qualification")),
        clinical_skills=_list(analysis.get("clinical_skills"))[:6],
        resume_score=resume_score,
        match_score=match_score,
        shortlist_recommendation=_recommendation(match_score),
        match_reasons=reasons[:5],
        recruiter_insights=_list(analysis.get("recruiter_insights"))[:4],
        candidate_summary=analysis.get("candidate_summary"),
    )


def _compare_candidate(candidate: CandidateMatch) -> CandidateComparison:
    strongest = candidate.match_reasons[0] if candidate.match_reasons else "Relevant healthcare profile."
    risk = "No major gaps detected."
    if candidate.experience_years is None:
        risk = "Experience needs manual verification."
    elif candidate.resume_score < 60:
        risk = "Resume score is moderate; review credentials closely."
    return CandidateComparison(
        candidate_id=candidate.id,
        name=candidate.name,
        experience_years=candidate.experience_years,
        specialization=candidate.specialization,
        score=candidate.match_score,
        strongest_signal=strongest,
        risk_or_gap=risk,
    )


def _shortlist_suggestions(candidates: list[CandidateMatch]) -> list[str]:
    strong = [candidate for candidate in candidates if candidate.match_score >= 80]
    if not candidates:
        return ["No matching candidates found. Broaden specialization or experience filters."]
    suggestions = [f"Shortlist {candidate.name} for first-round review." for candidate in strong[:3]]
    if not suggestions:
        suggestions.append(f"Start with {candidates[0].name}; they are the closest available match.")
    return suggestions


def _hiring_insights(candidates: list[CandidateMatch], intent: RecruiterSearchIntent) -> list[str]:
    if not candidates:
        return ["Talent pool is currently thin for this request."]
    specialties = Counter(candidate.specialization for candidate in candidates if candidate.specialization)
    avg_score = round(sum(candidate.match_score for candidate in candidates) / len(candidates))
    insights = [f"Average match score across matching candidates is {avg_score}%."]
    if intent.specialization:
        insights.append(f"{len(candidates)} candidates match the {intent.specialization} hiring intent.")
    if specialties:
        specialty, count = specialties.most_common(1)[0]
        insights.append(f"Most common candidate specialization is {specialty} ({count} profiles).")
    return insights


def _recommendation(score: int) -> str:
    if score >= 85:
        return "Priority shortlist"
    if score >= 70:
        return "Shortlist"
    if score >= 50:
        return "Review manually"
    return "Low match"


def _contains(value: object, expected: object) -> bool:
    return bool(value and expected and str(expected).lower() in str(value).lower())


def _candidate_search_text(record: ResumeRecord, analysis: dict) -> str:
    values = [
        analysis.get("name"),
        analysis.get("specialization"),
        analysis.get("sub_specialization"),
        analysis.get("current_employer"),
        analysis.get("research_experience"),
        analysis.get("teaching_experience"),
        analysis.get("candidate_summary"),
        getattr(record, "extracted_text", ""),
        *_list(analysis.get("qualification")),
        *_list(analysis.get("previous_employers")),
        *_list(analysis.get("clinical_skills")),
        *_list(analysis.get("technical_skills")),
        *_list(analysis.get("medical_certifications")),
        *_list(analysis.get("international_certifications")),
        *_list(analysis.get("recommended_roles")),
        *_list(analysis.get("recruiter_insights")),
    ]
    return " ".join(str(value).lower() for value in values if value)


def _query_terms(query: str) -> list[str]:
    text = query.lower()
    terms = re.findall(r"[a-z0-9][a-z0-9+#.-]*", text)
    stop_words = {
        "show",
        "me",
        "top",
        "find",
        "search",
        "candidate",
        "candidates",
        "with",
        "and",
        "or",
        "the",
        "for",
        "years",
        "year",
        "yrs",
        "experience",
    }
    return [term for term in terms if term not in stop_words and not term.isdigit()]


def _list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str) and value:
        return [value]
    return []


def _number_or_none(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
