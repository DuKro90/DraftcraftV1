"""Async task executor abstraction for Cloud Tasks or Celery fallback."""
import json
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class AsyncExecutor:
    """Unified interface for async task execution.

    Routes between Google Cloud Tasks (production) and Celery (local/fallback).
    Uses feature flag CLOUD_TASKS_ENABLED to switch implementations.
    """

    @staticmethod
    def process_document(
        document_id: str,
        user_id: Optional[int] = None,
        batch_id: Optional[str] = None
    ) -> Optional[str]:
        """Queue document for async processing.

        Args:
            document_id: UUID of document to process
            user_id: ID of user who uploaded (optional)
            batch_id: UUID of batch job (optional)

        Returns:
            Task ID/name, or None if failed
        """
        payload = {
            'document_id': str(document_id),
            'user_id': user_id,
            'batch_id': str(batch_id) if batch_id else None,
        }

        return AsyncExecutor._execute_async_task('process_document', payload)

    @staticmethod
    def process_batch(
        batch_id: str,
        user_id: int
    ) -> Optional[str]:
        """Queue batch for async processing.

        Args:
            batch_id: UUID of batch job
            user_id: ID of user who created batch

        Returns:
            Task ID/name, or None if failed
        """
        payload = {
            'batch_id': str(batch_id),
            'user_id': user_id,
        }

        return AsyncExecutor._execute_async_task('process_batch', payload)

    @staticmethod
    def _execute_async_task(
        task_name: str,
        payload: Dict[str, Any]
    ) -> Optional[str]:
        """Execute task via Cloud Tasks or Celery.

        Args:
            task_name: Name of task to execute (e.g., 'process_document')
            payload: Task payload dictionary

        Returns:
            Task ID/name, or None if failed
        """
        # Check if Cloud Tasks is enabled and available
        use_cloud_tasks = getattr(settings, 'CLOUD_TASKS_ENABLED', False)

        if use_cloud_tasks:
            return AsyncExecutor._execute_cloud_task(task_name, payload)
        else:
            return AsyncExecutor._execute_celery_task(task_name, payload)

    @staticmethod
    def _execute_cloud_task(
        task_name: str,
        payload: Dict[str, Any]
    ) -> Optional[str]:
        """Execute task via Google Cloud Tasks.

        Args:
            task_name: Name of task
            payload: Task payload

        Returns:
            Cloud Task ID, or None if failed
        """
        try:
            from core.cloud_tasks_client import CloudTasksClient

            # Get GCP configuration from settings
            project_id = getattr(settings, 'GCP_PROJECT_ID', None)
            queue_name = getattr(settings, 'CLOUD_TASKS_QUEUE', 'document-processing')
            webhook_url = getattr(settings, 'CLOUD_TASKS_WEBHOOK_URL', None)

            if not project_id or not webhook_url:
                logger.warning(
                    "Cloud Tasks enabled but GCP_PROJECT_ID or CLOUD_TASKS_WEBHOOK_URL not configured. "
                    "Falling back to Celery."
                )
                return AsyncExecutor._execute_celery_task(task_name, payload)

            # Create Cloud Tasks client
            client = CloudTasksClient(
                project_id=project_id,
                queue=queue_name,
                webhook_url=webhook_url
            )

            # Create task
            task_id = client.create_task(
                payload=payload,
                task_name=None,  # Auto-generate
                in_seconds=0  # Immediate
            )

            if task_id:
                logger.info(f"Created Cloud Task: {task_id} for {task_name}")
            else:
                logger.error(f"Failed to create Cloud Task for {task_name}")

            return task_id

        except ImportError:
            logger.warning("google-cloud-tasks not installed, falling back to Celery")
            return AsyncExecutor._execute_celery_task(task_name, payload)
        except Exception as e:
            logger.error(f"Error executing Cloud Task: {str(e)}, falling back to Celery")
            return AsyncExecutor._execute_celery_task(task_name, payload)

    @staticmethod
    def _execute_celery_task(
        task_name: str,
        payload: Dict[str, Any]
    ) -> Optional[str]:
        """Execute task via Celery.

        Args:
            task_name: Name of task
            payload: Task payload

        Returns:
            Celery task ID, or None if failed
        """
        try:
            from extraction.tasks import (
                process_document_async,
                process_batch_async
            )

            # Route to correct Celery task
            if task_name == 'process_document':
                task = process_document_async.delay(
                    document_id=payload['document_id'],
                    user_id=payload.get('user_id'),
                    batch_id=payload.get('batch_id')
                )
                logger.info(f"Created Celery task {task.id} for {task_name}")
                return str(task.id)

            elif task_name == 'process_batch':
                task = process_batch_async.delay(
                    batch_id=payload['batch_id'],
                    user_id=payload['user_id']
                )
                logger.info(f"Created Celery task {task.id} for {task_name}")
                return str(task.id)

            else:
                logger.error(f"Unknown task: {task_name}")
                return None

        except ImportError as e:
            logger.error(f"Celery tasks not available: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error executing Celery task: {str(e)}")
            return None

    @staticmethod
    def is_available() -> bool:
        """Check if async execution is available.

        Returns:
            True if either Cloud Tasks or Celery is available
        """
        use_cloud_tasks = getattr(settings, 'CLOUD_TASKS_ENABLED', False)

        if use_cloud_tasks:
            try:
                from core.cloud_tasks_client import CloudTasksClient
                project_id = getattr(settings, 'GCP_PROJECT_ID', None)
                webhook_url = getattr(settings, 'CLOUD_TASKS_WEBHOOK_URL', None)
                return bool(project_id and webhook_url)
            except ImportError:
                return False

        else:
            # Check if Celery is available
            try:
                from extraction.tasks import process_document_async
                return True
            except ImportError:
                return False
