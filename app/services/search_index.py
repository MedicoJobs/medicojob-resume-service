from opensearchpy import OpenSearch

from app.core.config import Settings
from app.models.resume import ResumeAnalysis


class ResumeSearchIndexer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None

    @property
    def client(self):
        if self._client is None and self.settings.opensearch_host:
            self._client = OpenSearch(hosts=[self.settings.opensearch_host])
        return self._client

    def index(self, document_id: str, analysis: ResumeAnalysis, text: str) -> None:
        if not self.settings.enable_opensearch_indexing or self.client is None:
            return

        self.client.index(
            index=self.settings.opensearch_index,
            id=document_id,
            body={"analysis": analysis.model_dump(mode="json"), "text": text[:20000]},
        )
