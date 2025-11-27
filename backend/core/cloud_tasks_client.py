"""GCP Cloud Tasks client for async document processing."""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CloudTasksClient:
    """Client for interacting with GCP Cloud Tasks."""

    def __init__(
        self,
        project_id: str,
        queue: str,
        location: str = 'europe-west3',
        webhook_url: Optional[str] = None
    ):
        """Initialize Cloud Tasks client.

        Args:
            project_id: GCP project ID
            queue: Cloud Tasks queue name
            location: GCP region (default: europe-west3 for GDPR)
            webhook_url: Base URL for webhook callbacks
        """
        self.project_id = project_id
        self.queue = queue
        self.location = location
        self.webhook_url = webhook_url
        self.client = None
        self._initialize()

    def _initialize(self):
        """Initialize Cloud Tasks client."""
        try:
            from google.cloud import tasks_v2

            self.client = tasks_v2.CloudTasksClient()
            logger.info(f"CloudTasksClient initialized for project {self.project_id}")
        except ImportError:
            logger.warning(
                "google-cloud-tasks not installed. "
                "Install with: pip install google-cloud-tasks"
            )
            self.client = None
        except Exception as e:
            logger.warning(f"Failed to initialize Cloud Tasks client: {str(e)}")
            self.client = None

    def get_queue_path(self) -> str:
        """Get the full path to the Cloud Tasks queue.

        Returns:
            Queue path in format: projects/PROJECT_ID/locations/LOCATION/queues/QUEUE_NAME
        """
        return f"projects/{self.project_id}/locations/{self.location}/queues/{self.queue}"

    def create_task(
        self,
        payload: Dict[str, Any],
        task_name: Optional[str] = None,
        in_seconds: int = 0,
        http_method: str = "POST"
    ) -> Optional[str]:
        """Create a Cloud Task for async processing.

        Args:
            payload: Task payload as dictionary
            task_name: Optional task name (auto-generated if not provided)
            in_seconds: Delay before task execution (0 = immediate)
            http_method: HTTP method (default: POST)

        Returns:
            Task name/ID, or None if failed
        """
        if not self.client:
            logger.error("Cloud Tasks client not initialized")
            return None

        if not self.webhook_url:
            logger.error("Webhook URL not configured for Cloud Tasks")
            return None

        try:
            from google.cloud import tasks_v2
            from google.protobuf import timestamp_pb2

            # Prepare task
            task = {
                'http_request': {
                    'http_method': http_method,
                    'url': self.webhook_url,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Cloud-Task': 'true',
                    },
                    'body': json.dumps(payload).encode(),
                }
            }

            # Schedule for later if needed
            if in_seconds > 0:
                d = datetime.utcnow() + timedelta(seconds=in_seconds)
                timestamp = timestamp_pb2.Timestamp()
                timestamp.FromDatetime(d)
                task['schedule_time'] = timestamp

            # Create task with parent project/location/queue
            parent = self.client.queue_path(
                self.project_id,
                self.location,
                self.queue
            )

            response = self.client.create_task(request={'parent': parent, 'task': task})

            task_name = response.name
            logger.info(f"Created Cloud Task: {task_name}")
            return task_name

        except Exception as e:
            logger.error(f"Failed to create Cloud Task: {str(e)}")
            return None

    def get_task(self, task_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a Cloud Task.

        Args:
            task_name: Full task path or name

        Returns:
            Task information dictionary, or None if failed
        """
        if not self.client:
            logger.error("Cloud Tasks client not initialized")
            return None

        try:
            # Ensure we have full path
            if not task_name.startswith('projects/'):
                task_name = f"{self.get_queue_path()}/tasks/{task_name}"

            request = {'name': task_name}
            task = self.client.get_task(request=request)

            return {
                'name': task.name,
                'state': task.state,
                'create_time': task.create_time,
                'schedule_time': task.schedule_time,
            }

        except Exception as e:
            logger.warning(f"Failed to get task {task_name}: {str(e)}")
            return None

    def delete_task(self, task_name: str) -> bool:
        """Delete a Cloud Task.

        Args:
            task_name: Full task path or name

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Cloud Tasks client not initialized")
            return False

        try:
            # Ensure we have full path
            if not task_name.startswith('projects/'):
                task_name = f"{self.get_queue_path()}/tasks/{task_name}"

            request = {'name': task_name}
            self.client.delete_task(request=request)

            logger.info(f"Deleted Cloud Task: {task_name}")
            return True

        except Exception as e:
            logger.warning(f"Failed to delete task {task_name}: {str(e)}")
            return False

    def list_tasks(self) -> Optional[list]:
        """List all tasks in the queue.

        Returns:
            List of task names, or None if failed
        """
        if not self.client:
            logger.error("Cloud Tasks client not initialized")
            return None

        try:
            parent = self.get_queue_path()
            request = {'parent': parent}
            page_result = self.client.list_tasks(request=request)

            tasks = []
            for task in page_result:
                tasks.append(task.name)

            logger.debug(f"Listed {len(tasks)} tasks in queue")
            return tasks

        except Exception as e:
            logger.warning(f"Failed to list tasks: {str(e)}")
            return None

    def purge_queue(self) -> bool:
        """Purge all tasks from the queue.

        Args:
            None

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Cloud Tasks client not initialized")
            return False

        try:
            parent = self.get_queue_path()
            request = {'name': parent}
            self.client.purge_queue(request=request)

            logger.info(f"Purged queue: {parent}")
            return True

        except Exception as e:
            logger.warning(f"Failed to purge queue: {str(e)}")
            return False

    def is_available(self) -> bool:
        """Check if Cloud Tasks is available and configured.

        Returns:
            True if client is initialized and ready, False otherwise
        """
        return self.client is not None

    def get_queue_stats(self) -> Optional[Dict[str, Any]]:
        """Get queue statistics.

        Returns:
            Dictionary with queue info, or None if failed
        """
        if not self.client:
            logger.error("Cloud Tasks client not initialized")
            return None

        try:
            parent = self.get_queue_path()
            request = {'name': parent}
            queue = self.client.get_queue(request=request)

            return {
                'name': queue.name,
                'state': queue.state,
                'create_time': queue.create_time,
                'task_ttl': queue.task_ttl,
                'retry_config': {
                    'max_attempts': queue.retry_config.max_attempts,
                    'max_backoff': queue.retry_config.max_backoff,
                    'max_doublings': queue.retry_config.max_doublings,
                    'min_backoff': queue.retry_config.min_backoff,
                },
            }

        except Exception as e:
            logger.warning(f"Failed to get queue stats: {str(e)}")
            return None


class CloudTasksLocalFallback:
    """Local fallback for Cloud Tasks (uses Celery for local development)."""

    def __init__(self, project_id: str = None, queue: str = None, **kwargs):
        """Initialize fallback client (mocks Cloud Tasks behavior).

        Args:
            project_id: Project ID (ignored in local mode)
            queue: Queue name (ignored in local mode)
        """
        logger.info("Using local Celery fallback for Cloud Tasks")
        self.tasks = {}  # Store tasks locally

    def create_task(
        self,
        payload: Dict[str, Any],
        task_name: Optional[str] = None,
        in_seconds: int = 0,
        **kwargs
    ) -> Optional[str]:
        """Create a task locally (fallback).

        Args:
            payload: Task payload
            task_name: Optional task name
            in_seconds: Delay before execution

        Returns:
            Mock task ID
        """
        import uuid
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            'payload': payload,
            'created_at': datetime.utcnow(),
            'scheduled_for': datetime.utcnow() + timedelta(seconds=in_seconds),
        }
        logger.debug(f"Created local task: {task_id}")
        return task_id

    def get_task(self, task_name: str) -> Optional[Dict[str, Any]]:
        """Get task info (local fallback)."""
        if task_name in self.tasks:
            task = self.tasks[task_name]
            return {
                'name': task_name,
                'state': 'QUEUED',
                'create_time': task['created_at'],
                'schedule_time': task['scheduled_for'],
            }
        return None

    def delete_task(self, task_name: str) -> bool:
        """Delete task (local fallback)."""
        if task_name in self.tasks:
            del self.tasks[task_name]
            return True
        return False

    def list_tasks(self) -> list:
        """List all local tasks."""
        return list(self.tasks.keys())

    def purge_queue(self) -> bool:
        """Purge local tasks."""
        self.tasks.clear()
        return True

    def is_available(self) -> bool:
        """Always available locally."""
        return True

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get local queue stats."""
        return {
            'name': 'local-fallback',
            'state': 'RUNNING',
            'task_count': len(self.tasks),
        }


def get_cloud_tasks_client(
    use_fallback: bool = False,
    **kwargs
) -> CloudTasksClient:
    """Factory function to get Cloud Tasks client.

    Args:
        use_fallback: Use local Celery fallback if True
        **kwargs: Arguments for CloudTasksClient

    Returns:
        CloudTasksClient or CloudTasksLocalFallback instance
    """
    if use_fallback:
        return CloudTasksLocalFallback(**kwargs)

    return CloudTasksClient(**kwargs)
