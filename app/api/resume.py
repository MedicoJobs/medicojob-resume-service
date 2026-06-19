import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.workflow import ResumeIntelligenceWorkflow
from app.core.config import Settings, get_settings
from app.core.security import get_current_user
from app.db.models import ResumeRecord
from app.db.session import get_db
from app.models.copilot import CandidateDecisionRequest, CandidateProfileResponse, RecruiterCopilotRequest, RecruiterCopilotResponse
from app.models.interview import InterviewQuestionRequest, InterviewQuestionResponse, PracticeExamRequest, PracticeExamResponse
from app.models.resume import ResumeAnalysis
from app.services.document_extractor import extract_text, read_upload, validate_upload
from app.services.interview_question_agent import generate_interview_questions
from app.services.llm import ResumeLLMClient
from app.services.local_resume_store import save_local_resume_record
from app.services.candidate_decisions import save_candidate_decision
from app.services.applicant_exam_agent import generate_applicant_mcq_exam
from app.services.recruiter_copilot import get_candidate_profile, run_recruiter_copilot
from app.services.search_index import ResumeSearchIndexer
from app.services.storage import ResumeStorage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.post("/upload", response_model=ResumeAnalysis)
async def upload_resume(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ResumeAnalysis:
    return await _process_resume(file=file, user=user, db=db, settings=settings, persist=settings.persist_resume_analysis)


@router.post("/dev-upload", response_model=ResumeAnalysis)
async def dev_upload_resume(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> ResumeAnalysis:
    if settings.environment.lower() not in {"development", "local", "dev"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return await _process_resume(file=file, user={"sub": "local-dev"}, db=None, settings=settings, persist=False)


@router.post("/copilot/search", response_model=RecruiterCopilotResponse)
async def recruiter_copilot_search(
    payload: RecruiterCopilotRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecruiterCopilotResponse:
    role = str(user.get("role") or user.get("userType") or "").lower()
    if role and role not in {"hospital", "recruiter", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recruiter access required")
    return await run_recruiter_copilot(db=db, query=payload.query, limit=payload.limit)


@router.get("/copilot/candidates/{candidate_id}", response_model=CandidateProfileResponse)
async def recruiter_candidate_profile(
    candidate_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    role = str(user.get("role") or user.get("userType") or "").lower()
    if role and role not in {"hospital", "recruiter", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recruiter access required")
    hospital_id = str(user.get("id") or user.get("_id") or user.get("sub") or "")
    profile = await get_candidate_profile(db, candidate_id, hospital_id or None)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return profile


@router.post("/copilot/candidates/{candidate_id}/decision")
async def recruiter_candidate_decision(
    candidate_id: int,
    payload: CandidateDecisionRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    role = str(user.get("role") or user.get("userType") or "").lower()
    if role and role not in {"hospital", "recruiter", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recruiter access required")
    hospital_id = str(user.get("id") or user.get("_id") or user.get("sub") or "")
    profile = await get_candidate_profile(db, candidate_id, hospital_id or None)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    decision = save_candidate_decision(candidate_id, hospital_id or None, payload.status, payload.note)
    return {"message": "Candidate decision saved", "decision": decision}


@router.post("/interview/generate", response_model=InterviewQuestionResponse)
async def interview_question_generation(
    payload: InterviewQuestionRequest,
    user: dict = Depends(get_current_user),
) -> InterviewQuestionResponse:
    role = str(user.get("role") or user.get("userType") or "").lower()
    if role and role not in {"hospital", "recruiter", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hospital access required")
    return generate_interview_questions(payload)


@router.post("/interview/practice-exam", response_model=PracticeExamResponse)
async def applicant_practice_exam(
    payload: PracticeExamRequest,
    user: dict = Depends(get_current_user),
) -> PracticeExamResponse:
    role = str(user.get("role") or user.get("userType") or "").lower()
    if role and role not in {"applicant", "doctor", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Applicant access required")
    return generate_applicant_mcq_exam(payload)


async def _process_resume(
    file: UploadFile,
    user: dict,
    db: AsyncSession | None,
    settings: Settings,
    persist: bool,
) -> ResumeAnalysis:
    suffix = validate_upload(file)
    data = await read_upload(file, settings.max_upload_bytes)

    try:
        raw_text = extract_text(data, suffix)
    except Exception as exc:
        logger.exception("Resume text extraction failed")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unable to extract text from resume") from exc

    if not raw_text.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Resume contains no readable text")

    storage = ResumeStorage(settings)
    s3_key = storage.upload(data, Path(file.filename or "resume").name, file.content_type or "application/octet-stream")

    workflow = ResumeIntelligenceWorkflow(ResumeLLMClient(settings))
    analysis = await workflow.run(
        {
            "filename": file.filename or "resume",
            "content_type": file.content_type or "application/octet-stream",
            "raw_text": raw_text,
        }
    )

    if persist and db is not None:
        user_id = str(user.get("id") or user.get("_id") or user.get("sub") or "")
        record = ResumeRecord(
            user_id=user_id or None,
            filename=file.filename or "resume",
            content_type=file.content_type or "application/octet-stream",
            s3_key=s3_key,
            extracted_text=raw_text,
            analysis=analysis.model_dump(mode="json"),
        )
        db.add(record)
        try:
            await db.commit()
            await db.refresh(record)
            ResumeSearchIndexer(settings).index(str(record.id), analysis, raw_text)
        except Exception:
            logger.exception("Resume analysis database persistence failed; saving local fallback record")
            await db.rollback()
            save_local_resume_record(
                user_id=user_id or None,
                filename=file.filename or "resume",
                content_type=file.content_type or "application/octet-stream",
                s3_key=s3_key,
                extracted_text=raw_text,
                analysis=analysis,
            )
    return analysis
