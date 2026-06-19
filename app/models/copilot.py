from pydantic import BaseModel, Field


class RecruiterCopilotRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    limit: int = Field(default=5, ge=1, le=25)


class RecruiterSearchIntent(BaseModel):
    specialization: str | None = None
    min_experience_years: float | None = None
    skills: list[str] = Field(default_factory=list)
    location: str | None = None
    seniority_level: str | None = None


class CandidateMatch(BaseModel):
    id: int
    name: str
    specialization: str | None = None
    experience_years: float | None = None
    location: str | None = None
    current_employer: str | None = None
    qualification: list[str] = Field(default_factory=list)
    clinical_skills: list[str] = Field(default_factory=list)
    resume_score: int = 0
    match_score: int = Field(ge=0, le=100)
    shortlist_recommendation: str
    match_reasons: list[str] = Field(default_factory=list)
    recruiter_insights: list[str] = Field(default_factory=list)
    candidate_summary: str | None = None


class CandidateComparison(BaseModel):
    candidate_id: int
    name: str
    experience_years: float | None = None
    specialization: str | None = None
    score: int
    strongest_signal: str
    risk_or_gap: str


class RecruiterCopilotResponse(BaseModel):
    query: str
    intent: RecruiterSearchIntent
    total_candidates: int
    returned_candidates: int
    best_match_score: int
    top_candidates: list[CandidateMatch] = Field(default_factory=list)
    comparison: list[CandidateComparison] = Field(default_factory=list)
    shortlist_suggestions: list[str] = Field(default_factory=list)
    hiring_insights: list[str] = Field(default_factory=list)


class CandidateDecisionRequest(BaseModel):
    status: str = Field(..., pattern="^(shortlisted|rejected)$")
    note: str = Field(..., min_length=2, max_length=1000)


class CandidateProfileResponse(BaseModel):
    id: int
    user_id: str | None = None
    filename: str | None = None
    analysis: dict = Field(default_factory=dict)
    extracted_text_preview: str = ""
    decision: dict | None = None
