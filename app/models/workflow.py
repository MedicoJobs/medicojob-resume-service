from typing import Any, TypedDict

from app.models.resume import ResumeAnalysis


class ResumeWorkflowState(TypedDict, total=False):
    filename: str
    content_type: str
    raw_text: str
    clean_text: str
    extraction: dict[str, Any]
    analysis: ResumeAnalysis
    errors: list[str]
