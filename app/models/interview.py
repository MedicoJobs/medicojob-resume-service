from pydantic import BaseModel, Field


class InterviewQuestionRequest(BaseModel):
    position: str = Field(..., min_length=2, max_length=160)
    specialization: str | None = Field(default=None, max_length=120)
    seniority: str | None = Field(default=None, max_length=80)


class InterviewQuestion(BaseModel):
    question: str
    focus: str
    expected_signal: str


class ClinicalCaseStudy(BaseModel):
    title: str
    prompt: str
    evaluation_points: list[str] = Field(default_factory=list)


class ScoringRubricItem(BaseModel):
    criterion: str
    weight: int = Field(ge=0, le=100)
    strong_signal: str
    concern_signal: str


class InterviewQuestionResponse(BaseModel):
    position: str
    role_family: str
    technical_questions: list[InterviewQuestion] = Field(default_factory=list)
    scenario_questions: list[InterviewQuestion] = Field(default_factory=list)
    clinical_case_studies: list[ClinicalCaseStudy] = Field(default_factory=list)
    behavioral_questions: list[InterviewQuestion] = Field(default_factory=list)
    scoring_rubric: list[ScoringRubricItem] = Field(default_factory=list)
    interviewer_tips: list[str] = Field(default_factory=list)


class PracticeExamRequest(BaseModel):
    position: str = Field(..., min_length=2, max_length=160)
    specialization: str | None = Field(default=None, max_length=120)
    difficulty: str = Field(default="medium", max_length=40)
    question_count: int = Field(default=8, ge=3, le=15)


class PracticeExamQuestion(BaseModel):
    id: int
    type: str
    question: str
    options: list[str] = Field(default_factory=list)
    correct_answer: str | None = None
    explanation: str
    scoring_points: list[str] = Field(default_factory=list)


class PracticeExamResponse(BaseModel):
    attempt_id: str
    position: str
    role_family: str
    difficulty: str
    questions: list[PracticeExamQuestion] = Field(default_factory=list)
