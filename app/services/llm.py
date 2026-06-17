import json
import logging
from typing import Any

from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You extract structured healthcare resume data for recruiters.
Return valid JSON only. Do not include markdown, commentary, or inferred facts that conflict with the resume.
Use null for unknown scalar values and [] for unknown lists."""

USER_PROMPT = """Extract the requested fields from this resume and return JSON matching these keys:
name,email,phone,location,education,qualification,specialization,sub_specialization,experience_years,
current_employer,previous_employers,nmc_registration,state_medical_council_registration,
nursing_council_registration,publications_count,research_experience,teaching_experience,clinical_skills,
technical_skills,languages_known,medical_certifications,international_certifications.

Resume:
{resume_text}
"""


class ResumeLLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = ChatBedrock(
                model_id=self.settings.bedrock_model_id,
                region_name=self.settings.aws_region,
                model_kwargs={"temperature": 0, "max_tokens": 3000},
            )
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def extract(self, resume_text: str) -> dict[str, Any]:
        if not self.settings.enable_llm:
            return {}

        response = await self.client.ainvoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=USER_PROMPT.format(resume_text=resume_text[:24000])),
            ]
        )
        content = response.content if isinstance(response.content, str) else json.dumps(response.content)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Bedrock returned non-JSON content")
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                return json.loads(content[start : end + 1])
            raise
