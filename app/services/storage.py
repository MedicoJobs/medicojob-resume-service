from uuid import uuid4

import boto3

from app.core.config import Settings


class ResumeStorage:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client("s3", region_name=self.settings.aws_region)
        return self._client

    def upload(self, data: bytes, filename: str, content_type: str) -> str | None:
        if not self.settings.enable_s3_upload:
            return None

        key = f"resumes/{uuid4()}-{filename}"
        self.client.put_object(Bucket=self.settings.s3_bucket, Key=key, Body=data, ContentType=content_type)
        return key
