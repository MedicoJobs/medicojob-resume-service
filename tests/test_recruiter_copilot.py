from types import SimpleNamespace

from app.services.recruiter_copilot import _build_candidate_match, parse_recruiter_query


def test_parse_recruiter_query_extracts_specialization_and_experience():
    intent = parse_recruiter_query("Show me top cardiologists with 10+ years experience")

    assert intent.specialization == "Cardiology"
    assert intent.min_experience_years == 10


def test_candidate_match_prioritizes_requested_specialist():
    intent = parse_recruiter_query("Show me top cardiologists with 10+ years experience")
    record = SimpleNamespace(
        id=7,
        analysis={
            "name": "Dr. Asha Rao",
            "specialization": "Cardiology",
            "experience_years": 12,
            "resume_score": 90,
            "nmc_registration": "NMC-123",
            "clinical_skills": ["Interventional cardiology", "Echocardiography"],
        },
    )

    candidate = _build_candidate_match(record, intent, "Show me top cardiologists with 10+ years experience")

    assert candidate.name == "Dr. Asha Rao"
    assert candidate.match_score >= 90
    assert candidate.shortlist_recommendation == "Priority shortlist"


def test_candidate_match_uses_resume_keywords_and_recommended_roles():
    intent = parse_recruiter_query("show me Resident Doctor")
    record = SimpleNamespace(
        id=11,
        extracted_text="MBBS fresher profile seeking resident doctor role in a hospital.",
        analysis={
            "name": "Dr. Kiran Shah",
            "specialization": "General Medicine",
            "experience_years": 0,
            "resume_score": 68,
            "recommended_roles": ["Resident Doctor", "Medical Officer"],
        },
    )

    candidate = _build_candidate_match(record, intent, "show me Resident Doctor", ["resident", "doctor"])

    assert candidate.match_score >= 35
    assert "Keyword match" in candidate.match_reasons[0]
