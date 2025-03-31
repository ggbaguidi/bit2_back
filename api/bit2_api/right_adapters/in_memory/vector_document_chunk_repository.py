# pylint: disable=dangerous-default-value
from typing import List
from uuid import uuid4

from phytov_api.core.domain.commands import CreateDocumentChunkCommand
from phytov_api.core.domain.models import DocumentChunk
from phytov_api.core.ports import IDocumentChunkRepository


class InMemoryVectorDocumentChunkRepository(IDocumentChunkRepository):
    def __init__(
        self,
        document_chunks: List[dict] = [],
    ) -> None:
        self.document_chunks = document_chunks

    def create(
        self, command: CreateDocumentChunkCommand, db_session=None
    ) -> DocumentChunk:
        """Method to add a new document chunk to the in-memory storage"""
        document_chunk = DocumentChunk(
            id_=str(uuid4()),
            document_id=command.document_id,
            chunk_index=command.chunk_index,
            text=command.text,
            embedding=command.embedding,
        )
        self.document_chunks.append(self.from_model(document_chunk))
        return document_chunk

    @staticmethod
    def to_model(item) -> DocumentChunk:
        """Method to convert from dict to domain model"""
        return DocumentChunk(
            id_=item["id"],
            document_id=item["document_id"],
            chunk_index=item["chunk_index"],
            text=item["text"],
            embedding=item["embedding"],
        )

    @staticmethod
    def from_model(item: DocumentChunk) -> dict:
        """Method to convert from domain model to dict"""
        return {
            "id": item.id_,
            "document_id": item.document_id,
            "chunk_index": item.chunk_index,
            "text": item.text,
            "embedding": item.embedding,
        }
