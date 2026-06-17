from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from app.models.resume import ResumeAnalysis, SeniorityLevel
from app.models.workflow import ResumeWorkflowState
from app.services.document_extractor import clean_text
from app.services.fallback_extractor import fallback_extract
from app.services.llm import ResumeLLMClient


class ResumeIntelligenceWorkflow:
    def __init__(self, llm_client: ResumeLLMClient):
        self.llm_client = llm_client
        self.graph = self._build_graph().compile()

    async def run(self, state: ResumeWorkflowState) -> ResumeAnalysis:
        result = await self.graph.ainvoke(state)
        return result["analysis"]

    def _build_graph(self):
        graph = StateGraph(ResumeWorkflowState)
        graph.add_node("document_extraction_agent", self.document_extraction_agent)
        graph.add_node("healthcare_information_extraction_agent", self.healthcare_information_extraction_agent)
        graph.add_node("resume_scoring_agent", self.resume_scoring_agent)
        graph.add_node("job_recommendation_agent", self.job_recommendation_agent)
        graph.add_node("profile_summary_agent", self.profile_summary_agent)

        graph.set_entry_point("document_extraction_agent")
        graph.add_edge("document_extraction_agent", "healthcare_information_extraction_agent")
        graph.add_edge("healthcare_information_extraction_agent", "resume_scoring_agent")
        graph.add_edge("resume_scoring_agent", "job_recommendation_agent")
        graph.add_edge("job_recommendation_agent", "profile_summary_agent")
        graph.add_edge("profile_summary_agent", END)
        return graph

    async def document_extraction_agent(self, state: ResumeWorkflowState) -> ResumeWorkflowState:
        state["clean_text"] = clean_text(state.get("raw_text", ""))
        return state

    async def healthcare_information_extraction_agent(self, state: ResumeWorkflowState) -> ResumeWorkflowState:
        text = state.get("clean_text", "")
        fallback = fallback_extract(text)
        try:
            llm_data = await self.llm_client.extract(text)
        except Exception as exc:
            state["errors"] = [*state.get("errors", []), f"LLM extraction failed: {exc}"]
            llm_data = {}
        merged = {**fallback, **{k: v for k, v in llm_data.items() if v not in (None, "", [])}}
        analysis = ResumeAnalysis(**_normalize_payload(merged))
        analysis.raw_ai_payload = llm_data or None
        analysis.missing_information = _missing_information(analysis)
        state["extraction"] = merged
        state["analysis"] = analysis
        return state

    async def resume_scoring_agent(self, state: ResumeWorkflowState) -> ResumeWorkflowState:
        analysis = state["analysis"]
        score = 0
        score += 25 if analysis.qualification else 0
        score += min(int((analysis.experience_years or 0) * 4), 25)
        score += 15 if analysis.specialization else 0
        score += 10 if analysis.nmc_registration or analysis.state_medical_council_registration or analysis.nursing_council_registration else 0
        score += min((len(analysis.medical_certifications) + len(analysis.international_certifications)) * 5, 10)
        score += min((analysis.publications_count or 0) * 2, 10)
        score += 5 if analysis.clinical_skills or analysis.technical_skills else 0
        analysis.resume_score = max(0, min(score, 100))
        analysis.strengths = _strengths(analysis)
        analysis.seniority_level = _seniority(analysis.experience_years)
        return state

    async def job_recommendation_agent(self, state: ResumeWorkflowState) -> ResumeWorkflowState:
        analysis = state["analysis"]
        analysis.recommended_roles = _recommended_roles(analysis)
        return state

    async def profile_summary_agent(self, state: ResumeWorkflowState) -> ResumeWorkflowState:
        analysis = state["analysis"]
        name = analysis.name or "This candidate"
        specialty = analysis.specialization or "healthcare"
        years = analysis.experience_years
        exp = "a fresher profile" if not years else f"{years:g} years of experience"
        analysis.candidate_summary = f"{name} is a {specialty} professional with {exp}."
        analysis.recruiter_insights = [
            insight
            for insight in [
                f"Seniority assessed as {analysis.seniority_level.value}.",
                "Registration details are present." if not any("Registration" in item for item in analysis.missing_information) else "Verify missing registration details before shortlisting.",
                f"Resume score is {analysis.resume_score}/100.",
            ]
            if insight
        ]
        return state


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("qualification"), str):
        payload["qualification"] = [payload["qualification"]]
    for key in ("previous_employers", "clinical_skills", "technical_skills", "languages_known", "medical_certifications", "international_certifications"):
        if isinstance(payload.get(key), str):
            payload[key] = [payload[key]]
    return payload


def _missing_information(analysis: ResumeAnalysis) -> list[str]:
    has_graduation_year = any(item.graduation_year for item in analysis.education)
    checks = {
        "Full Name Missing": analysis.name,
        "Email Missing": analysis.email,
        "Phone Number Missing": analysis.phone,
        "Specialization Missing": analysis.specialization,
        "Experience Missing": analysis.experience_years,
        "NMC Registration Missing": analysis.nmc_registration or analysis.state_medical_council_registration or analysis.nursing_council_registration,
        "Graduation Year Missing": has_graduation_year,
    }
    return [label for label, value in checks.items() if not value]


def _strengths(analysis: ResumeAnalysis) -> list[str]:
    strengths = []
    if analysis.qualification:
        strengths.append("Relevant healthcare qualifications")
    if analysis.experience_years and analysis.experience_years >= 5:
        strengths.append("Strong clinical experience")
    if analysis.publications_count:
        strengths.append("Academic publication record")
    if analysis.medical_certifications or analysis.international_certifications:
        strengths.append("Additional certifications")
    return strengths


def _seniority(years: float | None) -> SeniorityLevel:
    if years is None or years < 1:
        return SeniorityLevel.fresher
    if years < 3:
        return SeniorityLevel.junior
    if years < 7:
        return SeniorityLevel.mid_level
    if years < 12:
        return SeniorityLevel.senior
    return SeniorityLevel.expert


def _recommended_roles(analysis: ResumeAnalysis) -> list[str]:
    specialty = analysis.specialization or "Medical"
    if analysis.seniority_level in {SeniorityLevel.senior, SeniorityLevel.expert}:
        roles = [f"Consultant {specialty}", f"Associate Professor - {specialty}"]
    elif analysis.seniority_level == SeniorityLevel.mid_level:
        roles = [f"Senior Resident - {specialty}", f"Registrar - {specialty}"]
    elif analysis.seniority_level == SeniorityLevel.junior:
        roles = [f"Junior Resident - {specialty}", "Medical Officer"]
    else:
        roles = ["Resident Doctor", "Medical Officer"]
    if "Nursing" in " ".join(analysis.qualification + [specialty]):
        roles = ["Staff Nurse", "Nursing Officer", "Clinical Nurse Specialist"]
    return roles
