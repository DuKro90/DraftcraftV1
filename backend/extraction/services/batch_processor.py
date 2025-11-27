"""Batch document processor for managing bulk document uploads and processing."""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User

from documents.models import Batch, BatchDocument, Document
from extraction.async_executor import AsyncExecutor
from extraction.services.base_service import ExtractionServiceError

logger = logging.getLogger(__name__)


class BatchProcessorError(ExtractionServiceError):
    """Batch processor specific error."""
    pass


class BatchProcessor:
    """Orchestrate batch document processing with progress tracking.

    Manages:
    - Batch job creation and status tracking
    - Document queuing and retry logic
    - Progress calculation and reporting
    - Error handling and recovery
    """

    # Default retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 300  # 5 minutes
    BATCH_TIMEOUT_HOURS = 24

    def __init__(self, user: User):
        """Initialize batch processor for a specific user.

        Args:
            user: Django user performing the batch operation
        """
        self.user = user
        self.logger = logging.getLogger(f"{__name__}.{user.username}")

    def create_batch(
        self,
        name: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Batch:
        """Create a new batch job.

        Args:
            name: Human-readable batch name
            description: Optional description
            metadata: Optional additional metadata

        Returns:
            Created Batch instance

        Raises:
            BatchProcessorError: If batch creation fails
        """
        try:
            batch = Batch.objects.create(
                user=self.user,
                name=name,
                description=description,
                status='pending',
                file_count=0,
                processed_count=0,
                error_count=0,
                metadata=metadata or {}
            )

            self.logger.info(f"Created batch {batch.id} with name '{name}'")
            return batch

        except Exception as e:
            error_msg = f"Failed to create batch: {str(e)}"
            self.logger.error(error_msg)
            raise BatchProcessorError(error_msg)

    def add_documents_to_batch(
        self,
        batch: Batch,
        document_ids: List[str]
    ) -> Tuple[int, int]:
        """Add documents to a batch for processing.

        Args:
            batch: Batch instance
            document_ids: List of document UUIDs to add

        Returns:
            Tuple of (added_count, failed_count)

        Raises:
            BatchProcessorError: If batch is not in valid state
        """
        if batch.status not in ['pending', 'partial_failure']:
            raise BatchProcessorError(
                f"Cannot add documents to batch with status '{batch.status}'"
            )

        added_count = 0
        failed_count = 0

        try:
            with transaction.atomic():
                for doc_id in document_ids:
                    try:
                        # Check document exists and belongs to user
                        doc = Document.objects.get(id=doc_id, user=self.user)

                        # Avoid duplicates
                        exists = BatchDocument.objects.filter(
                            batch=batch,
                            document=doc
                        ).exists()

                        if exists:
                            self.logger.debug(
                                f"Document {doc_id} already in batch {batch.id}"
                            )
                            continue

                        # Create BatchDocument entry
                        BatchDocument.objects.create(
                            batch=batch,
                            document=doc,
                            status='pending'
                        )

                        added_count += 1

                    except Document.DoesNotExist:
                        self.logger.warning(
                            f"Document {doc_id} not found or not owned by user"
                        )
                        failed_count += 1
                    except Exception as e:
                        self.logger.error(
                            f"Error adding document {doc_id} to batch: {str(e)}"
                        )
                        failed_count += 1

                # Update batch file count
                batch.file_count = BatchDocument.objects.filter(
                    batch=batch
                ).count()
                batch.save(update_fields=['file_count'])

            self.logger.info(
                f"Added {added_count} documents to batch {batch.id} "
                f"({failed_count} failed)"
            )

            return added_count, failed_count

        except Exception as e:
            error_msg = f"Error adding documents to batch: {str(e)}"
            self.logger.error(error_msg)
            raise BatchProcessorError(error_msg)

    def start_processing(self, batch: Batch) -> int:
        """Start async processing for all documents in batch.

        Args:
            batch: Batch to process

        Returns:
            Number of tasks successfully queued

        Raises:
            BatchProcessorError: If batch cannot be processed
        """
        if batch.status != 'pending':
            raise BatchProcessorError(
                f"Cannot process batch with status '{batch.status}'"
            )

        if batch.file_count == 0:
            raise BatchProcessorError("Batch has no documents to process")

        try:
            # Mark batch as processing
            batch.status = 'processing'
            batch.save(update_fields=['status'])

            # Queue all pending documents
            batch_docs = BatchDocument.objects.filter(
                batch=batch,
                status='pending'
            )

            queued_count = 0
            for batch_doc in batch_docs:
                try:
                    # Queue document for processing
                    task_id = AsyncExecutor.process_document(
                        document_id=batch_doc.document.id,
                        user_id=self.user.id,
                        batch_id=batch.id
                    )

                    if task_id:
                        # Update BatchDocument with task reference
                        batch_doc.status = 'queued'
                        batch_doc.cloud_task_id = task_id
                        batch_doc.save(
                            update_fields=['status', 'cloud_task_id']
                        )
                        queued_count += 1
                    else:
                        # Task queuing failed
                        batch_doc.status = 'failed'
                        batch_doc.error_message = "Failed to queue task"
                        batch_doc.save(
                            update_fields=['status', 'error_message']
                        )
                        self.logger.warning(
                            f"Failed to queue document {batch_doc.document.id}"
                        )

                except Exception as e:
                    batch_doc.status = 'failed'
                    batch_doc.error_message = str(e)
                    batch_doc.save(
                        update_fields=['status', 'error_message']
                    )
                    self.logger.error(
                        f"Error queuing document {batch_doc.document.id}: {str(e)}"
                    )

            # Set estimated completion time
            avg_time_per_doc = 10  # seconds (optimistic estimate)
            estimated_duration = queued_count * avg_time_per_doc
            batch.estimated_completion = timezone.now() + timedelta(
                seconds=estimated_duration
            )
            batch.save(update_fields=['estimated_completion'])

            self.logger.info(
                f"Queued {queued_count}/{batch.file_count} documents in batch {batch.id}"
            )

            return queued_count

        except Exception as e:
            # Mark batch as failed if queuing failed
            batch.status = 'failed'
            batch.save(update_fields=['status'])
            error_msg = f"Error starting batch processing: {str(e)}"
            self.logger.error(error_msg)
            raise BatchProcessorError(error_msg)

    def update_document_status(
        self,
        batch_doc_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Update status of a document in batch (called by webhook/worker).

        Args:
            batch_doc_id: UUID of BatchDocument
            status: New status ('processing', 'completed', 'failed')
            error_message: Error message if status is 'failed'

        Raises:
            BatchProcessorError: If document not found
        """
        try:
            batch_doc = BatchDocument.objects.get(id=batch_doc_id)

            # Update document status
            batch_doc.status = status
            if error_message:
                batch_doc.error_message = error_message
            if status in ['completed', 'failed']:
                batch_doc.processed_at = timezone.now()

            batch_doc.save()

            # Update parent batch progress
            self._update_batch_progress(batch_doc.batch)

            self.logger.info(
                f"Updated BatchDocument {batch_doc_id} to status '{status}'"
            )

        except BatchDocument.DoesNotExist:
            error_msg = f"BatchDocument {batch_doc_id} not found"
            self.logger.error(error_msg)
            raise BatchProcessorError(error_msg)

    def _update_batch_progress(self, batch: Batch) -> None:
        """Update batch progress counters and overall status.

        Args:
            batch: Batch to update
        """
        # Calculate progress
        all_docs = BatchDocument.objects.filter(batch=batch)
        completed = all_docs.filter(status='completed').count()
        failed = all_docs.filter(status='failed').count()
        total = all_docs.count()

        # Update counts
        batch.processed_count = completed
        batch.error_count = failed

        # Determine overall status
        if completed + failed == total:
            # All documents processed
            if failed == 0:
                batch.status = 'completed'
            elif failed < total:
                batch.status = 'partial_failure'
            else:
                batch.status = 'failed'

            batch.completed_at = timezone.now()

        batch.save(
            update_fields=['processed_count', 'error_count', 'status', 'completed_at']
        )

    def get_batch_status(self, batch: Batch) -> Dict[str, Any]:
        """Get detailed batch status and progress.

        Args:
            batch: Batch instance

        Returns:
            Dictionary with batch status information
        """
        try:
            batch_docs = BatchDocument.objects.filter(batch=batch)

            status_breakdown = {
                'pending': batch_docs.filter(status='pending').count(),
                'queued': batch_docs.filter(status='queued').count(),
                'processing': batch_docs.filter(status='processing').count(),
                'completed': batch_docs.filter(status='completed').count(),
                'failed': batch_docs.filter(status='failed').count(),
            }

            return {
                'batch_id': str(batch.id),
                'name': batch.name,
                'status': batch.status,
                'file_count': batch.file_count,
                'processed_count': batch.processed_count,
                'error_count': batch.error_count,
                'progress_percentage': batch.progress_percentage,
                'status_breakdown': status_breakdown,
                'created_at': batch.created_at.isoformat(),
                'updated_at': batch.updated_at.isoformat(),
                'completed_at': batch.completed_at.isoformat() if batch.completed_at else None,
                'estimated_completion': batch.estimated_completion.isoformat() if batch.estimated_completion else None,
            }

        except Exception as e:
            self.logger.error(f"Error getting batch status: {str(e)}")
            return {}

    def get_batch_errors(
        self,
        batch: Batch,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get list of errors from batch processing.

        Args:
            batch: Batch instance
            limit: Maximum number of errors to return

        Returns:
            List of error records
        """
        try:
            failed_docs = BatchDocument.objects.filter(
                batch=batch,
                status='failed'
            ).select_related('document')[:limit]

            errors = []
            for batch_doc in failed_docs:
                errors.append({
                    'batch_document_id': str(batch_doc.id),
                    'document_id': str(batch_doc.document.id),
                    'document_name': batch_doc.document.original_filename,
                    'error_message': batch_doc.error_message,
                    'processed_at': batch_doc.processed_at.isoformat() if batch_doc.processed_at else None,
                })

            return errors

        except Exception as e:
            self.logger.error(f"Error getting batch errors: {str(e)}")
            return []

    def cancel_batch(self, batch: Batch) -> bool:
        """Cancel a batch that hasn't completed.

        Args:
            batch: Batch to cancel

        Returns:
            True if successful
        """
        if batch.status in ['completed', 'failed']:
            self.logger.warning(
                f"Cannot cancel batch {batch.id} with status '{batch.status}'"
            )
            return False

        try:
            # Mark batch as failed
            batch.status = 'failed'
            batch.completed_at = timezone.now()
            batch.save(update_fields=['status', 'completed_at'])

            # Mark all queued/processing documents as cancelled
            BatchDocument.objects.filter(
                batch=batch,
                status__in=['queued', 'processing']
            ).update(
                status='failed',
                error_message='Batch was cancelled',
                processed_at=timezone.now()
            )

            self.logger.info(f"Cancelled batch {batch.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error cancelling batch: {str(e)}")
            return False

    def retry_failed_document(
        self,
        batch_doc_id: str
    ) -> Optional[str]:
        """Retry processing a failed document in a batch.

        Args:
            batch_doc_id: UUID of BatchDocument to retry

        Returns:
            New task ID if successful, None otherwise
        """
        try:
            batch_doc = BatchDocument.objects.get(id=batch_doc_id)

            if batch_doc.status != 'failed':
                self.logger.warning(
                    f"Cannot retry non-failed document {batch_doc_id}"
                )
                return None

            # Queue document again
            task_id = AsyncExecutor.process_document(
                document_id=batch_doc.document.id,
                user_id=self.user.id,
                batch_id=batch_doc.batch.id
            )

            if task_id:
                batch_doc.status = 'queued'
                batch_doc.cloud_task_id = task_id
                batch_doc.error_message = ""
                batch_doc.save(
                    update_fields=['status', 'cloud_task_id', 'error_message']
                )
                self.logger.info(f"Retried document {batch_doc_id}, new task: {task_id}")
                return task_id
            else:
                self.logger.error(f"Failed to queue retry for document {batch_doc_id}")
                return None

        except BatchDocument.DoesNotExist:
            self.logger.error(f"BatchDocument {batch_doc_id} not found")
            return None
        except Exception as e:
            self.logger.error(f"Error retrying document: {str(e)}")
            return None
