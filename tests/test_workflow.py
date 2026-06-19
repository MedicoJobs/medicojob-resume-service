import pytest

from app.agents.workflow import ResumeIntelligenceWorkflow


class FakeLLM:
    async def extract(self, resume_text: str):
        return {}


@pytest.mark.asyncio
async def test_workflow_extracts_and_scores_healthcare_resume():
    workflow = ResumeIntelligenceWorkflow(FakeLLM())
    analysis = await workflow.run(
        {
            "filename": "resume.txt",
            "content_type": "text/plain",
            "raw_text": "Dr. John Doe\njohn@example.com\n+919876543210\nMBBS MD DM Cardiology\n8 years of experience\nNMC Registration: 123456",
        }
    )

    assert analysis.email == "john@example.com"
    assert analysis.specialization == "Cardiology"
    assert analysis.experience_years == 8
    assert analysis.seniority_level.value == "Senior"
    assert "Consultant Cardiology" in analysis.recommended_roles
    assert analysis.resume_score > 50


@pytest.mark.asyncio
async def test_workflow_scores_internal_medicine_resume_with_local_extractor():
    workflow = ResumeIntelligenceWorkflow(FakeLLM())
    analysis = await workflow.run(
        {
            "filename": "resume.txt",
            "content_type": "text/plain",
            "raw_text": """Dr. Kajapathy M., MBBS, MD (Internal Medicine)
Email: kajapathy.m@example.com | Phone: +91 98765 12345
Dedicated Internal Medicine Physician with 5 years of clinical experience.
Skills
Clinical Diagnosis, Internal Medicine, Emergency Care, Patient Management, EHR Systems, Critical Care
Certifications
ACLS, BLS, Hospital Infection Control Certification
Publications
Author of research papers on chronic disease management.
""",
        }
    )

    assert analysis.phone == "+91 98765 12345"
    assert analysis.specialization == "Internal Medicine"
    assert analysis.experience_years == 5
    assert "Clinical Diagnosis" in analysis.clinical_skills
    assert "ACLS" in analysis.medical_certifications
    assert analysis.resume_score > 60
