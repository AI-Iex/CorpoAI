import logging
from uuid import UUID
from app.dependencies.services import create_document_service

logger = logging.getLogger(__name__)


async def process_document_task(document_id: UUID) -> None:
    """
    Background task to process an uploaded document.

    1. Extracts text from the document
    2. Splits into chunks
    3. Generates embeddings
    4. Stores in ChromaDB
    5. Updates document status in PostgreSQL

    """
    logger.info(f"Starting background processing for document {document_id}")

    document_service = create_document_service()

    document = await document_service.process_document(document_id)

    if document.status.value == "completed":
        logger.info(
            f"Document {document_id} processed successfully",
            extra={"num_chunks": document.num_chunks},
        )
    else:
        logger.error(
            f"Document {document_id} processing failed",
            extra={"error": document.error_message},
        )
