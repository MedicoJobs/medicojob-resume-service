from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class SeniorityLevel(str, Enum):
    fresher = "Fresher"
    junior = "Junior"
    mid_level = "Mid-Level"
    senior = "Senior"
    expert = "Expert"


class EducationItem(BaseModel):
    degree: str | None = None
    institution: str | None = None
    graduation_year: int | None = None


class ResumeAnalysis(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    education: list[EducationItem] = Field(default_factory=list)
    qualification: list[str] = Field(default_factory=list)
    specialization: str | None = None
    sub_specialization: str | None = None
    experience_years: float | None = None
    current_employer: str | None = None
    previous_employers: list[str] = Field(default_factory=list)
    nmc_registration: str | None = None
    state_medical_council_registration: str | None = None
    nursing_council_registration: str | None = None
    publications_count: int | None = None
    research_experience: str | None = None
    teaching_experience: str | None = None
    clinical_skills: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    languages_known: list[str] = Field(default_factory=list)
    medical_certifications: list[str] = Field(default_factory=list)
    international_certifications: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    candidate_summary: str | None = None
    recruiter_insights: list[str] = Field(default_factory=list)
    seniority_level: SeniorityLevel = SeniorityLevel.fresher
    recommended_roles: list[str] = Field(default_factory=list)
    resume_score: int = Field(default=0, ge=0, le=100)
    missing_information: list[str] = Field(default_factory=list)
    raw_ai_payload: dict[str, Any] | None = None
