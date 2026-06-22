from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MedicoJobs Resume Intelligence Service"
    environment: str = "development"
    api_prefix: str = "/api/resume"
    max_upload_bytes: int = 10 * 1024 * 1024
    jwt_secret: str = "local-dev-secret"
    jwt_algorithm: str = "HS256"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/medicojobs_resume"

    aws_region: str = "ap-south-1"
    s3_bucket: str = "medicojobs-resumes"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    opensearch_host: str | None = None
    opensearch_index: str = "resume-intelligence"

    enable_s3_upload: bool = False
    enable_opensearch_indexing: bool = False
    enable_llm: bool = False
    persist_resume_analysis: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
