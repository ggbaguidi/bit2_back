# pylint: disable=dangerous-default-value
import json
from typing import List
from uuid import uuid4

from phytov_api.core.domain.commands.document import AddDocumentCommand
from phytov_api.core.domain.models.document import Document
from phytov_api.core.ports import IDocumentRepository


class InMemoryDocumentRepository(IDocumentRepository):
    def __init__(self, documents: List[dict] = []) -> None:
        self.documents = documents

    def create(self, command: AddDocumentCommand, db_session=None) -> Document:
        # Convert metadata dict to JSON string if it's a dict
        document_metadata = command.document_metadata
        if isinstance(document_metadata, dict):
            document_metadata = json.dumps(document_metadata)

        document = Document(
            id_=str(uuid4()),
            content=command.content,
            authors=command.authors,
            document_metadata=command.document_metadata,
            language=command.language if hasattr(command, "language") else None,
        )
        self.documents.append(self.from_model(document))
        return document

    @staticmethod
    def to_model(item: dict) -> Document:
        """Convert from dict to domain model"""
        return Document(
            id_=item["id"],
            content=item["content"],
            authors=item["authors"],
            document_metadata=item["document_metadata"],
            language=item.get("language"),
        )

    @staticmethod
    def from_model(item: Document) -> dict:
        """Convert from domain model to dict"""
        return {
            "id": item.id_,
            "content": item.content,
            "authors": item.authors,
            "document_metadata": item.document_metadata,
            "language": item.language,
        }
