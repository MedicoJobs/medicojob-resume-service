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
