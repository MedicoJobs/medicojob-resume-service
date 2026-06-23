# MedicoJobs Resume Intelligence Service

FastAPI service for extracting structured healthcare candidate data from PDF, DOCX, and TXT resumes.

## Endpoint






`POST /api/resume/upload`

Headers:
- `Authorization: Bearer <jwt>`

Form data:
- `file`: PDF, DOCX, or TXT resume up to 10 MB.

The response is JSON only and includes personal data, healthcare qualifications, registration details, scoring, missing information, summary, recruiter insights, and recommended roles.

## Local Run

Recommended:

```bash
cp .env.example .env
docker compose up --build
```

This service is tested with Python 3.12. Avoid Python 3.14 for local installs because `asyncpg` and `pydantic-core` may try to compile native wheels and fail without Visual C++ Build Tools.

Local PowerShell run with Python 3.12:

```powershell
.\scripts\start-local.ps1
```

For local tests without Bedrock:

```bash
set ENABLE_LLM=false
pytest
```

## Architecture

The LangGraph workflow has five nodes:

1. Document Extraction Agent: cleans and normalizes extracted text.
2. Healthcare Information Extraction Agent: calls Bedrock Claude Sonnet and merges deterministic fallback extraction.
3. Resume Scoring Agent: scores education, experience, registrations, skills, certifications, and publications.
4. Job Recommendation Agent: recommends healthcare roles from specialty and seniority.
5. Profile Summary Agent: generates summary and recruiter insights.

S3 upload and OpenSearch indexing are controlled by `ENABLE_S3_UPLOAD` and `ENABLE_OPENSEARCH_INDEXING`.
