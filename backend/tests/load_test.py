"""
Locust load test for DraftCraft API.

This module defines load test user types and tasks for testing the DraftCraft API
under various load scenarios. Three user types are defined to simulate realistic
usage patterns:

- ReadHeavyUser (60% of users): Primarily browse documents and proposals
- WriteHeavyUser (20% of users): Upload and process documents
- MixedUser (20% of users): Mix of all operations

Usage:
    # Warm-up test (10 users, 2 minutes)
    locust -f tests/load_test.py --host=http://localhost:8000 --headless \
        --users 10 --spawn-rate 2 --run-time 2m

    # Target load test (50 users, 5 minutes)
    locust -f tests/load_test.py --host=http://localhost:8000 --headless \
        --users 50 --spawn-rate 5 --run-time 5m

    # Stress test (100 users, 3 minutes)
    locust -f tests/load_test.py --host=http://localhost:8000 --headless \
        --users 100 --spawn-rate 10 --run-time 3m

    # Web UI (interactive mode)
    locust -f tests/load_test.py --host=http://localhost:8000
    # Then open http://localhost:8089 in browser
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from locust import HttpUser, TaskSet, task, between, events


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadTestConfig:
    """Centralized configuration for load testing."""

    # Authentication
    AUTH_ENDPOINT = "/api/auth/token/"
    USERNAME = os.getenv("LOADTEST_USERNAME", "loadtest_user")
    PASSWORD = os.getenv("LOADTEST_PASSWORD", "LoadTest2024!Secure")

    # API Endpoints
    DOCUMENTS_LIST = "/api/v1/documents/"
    DOCUMENTS_CREATE = "/api/v1/documents/"
    DOCUMENTS_PROCESS = "/api/v1/documents/{id}/process/"
    DOCUMENTS_RETRIEVE = "/api/v1/documents/{id}/"

    PROPOSALS_LIST = "/api/v1/proposals/"
    PROPOSALS_CREATE = "/api/v1/proposals/"

    HEALTH_CHECK = "/api/v1/health/ocr/"

    # Test data
    FIXTURES_DIR = Path(__file__).parent / "fixtures"
    LOADTEST_DATA_FILE = FIXTURES_DIR / "loadtest_data.json"
    SAMPLE_PDF_PATH = FIXTURES_DIR / "sample_load_test.pdf"

    # Performance thresholds (milliseconds)
    RESPONSE_TIME_THRESHOLD_MS = 2000  # Alert if response > 2 seconds

    @classmethod
    def load_fixtures(cls) -> dict:
        """Load test fixtures from JSON file."""
        if not cls.LOADTEST_DATA_FILE.exists():
            logger.warning(f"Fixtures file not found: {cls.LOADTEST_DATA_FILE}")
            return {}

        with open(cls.LOADTEST_DATA_FILE, 'r') as f:
            return json.load(f)


class DraftCraftBaseUser(HttpUser):
    """
    Base user class with authentication.

    All user types inherit from this class and automatically authenticate
    with the API using token-based authentication.
    """

    wait_time = between(1, 3)
    token: Optional[str] = None
    auth_headers: Optional[dict] = None
    document_ids: list = []

    def on_start(self) -> None:
        """Authenticate user and obtain API token."""
        logger.info(f"User {self.client_id} starting authentication")

        auth_data = {
            "username": LoadTestConfig.USERNAME,
            "password": LoadTestConfig.PASSWORD,
        }

        with self.client.post(
            LoadTestConfig.AUTH_ENDPOINT,
            json=auth_data,
            catch_response=True,
            name="[AUTH] Authenticate",
        ) as response:
            if response.status_code == 200:
                response_data = response.json()
                self.token = response_data.get("token")
                self.auth_headers = {"Authorization": f"Token {self.token}"}
                response.success()
                logger.info(f"User {self.client_id} authenticated successfully")
            else:
                response.failure(
                    f"Authentication failed with status {response.status_code}"
                )
                logger.error(f"User {self.client_id} authentication failed")
                raise Exception("Authentication failed")

    def get_document_list(self) -> list:
        """Fetch document list and extract IDs for use in other tasks."""
        with self.client.get(
            LoadTestConfig.DOCUMENTS_LIST,
            headers=self.auth_headers,
            catch_response=True,
            name="[READ] List Documents",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Handle both paginated and non-paginated responses
                    results = data.get("results", data.get("data", []))
                    if isinstance(results, list):
                        self.document_ids = [d.get("id") for d in results]
                    response.success()
                except Exception as e:
                    response.failure(f"Failed to parse document list: {e}")
                    logger.error(f"Failed to parse document list: {e}")
            else:
                response.failure(f"Failed to list documents: {response.status_code}")
                logger.error(f"Failed to list documents: {response.status_code}")

    def upload_document(self, filename: str = "sample_load_test.pdf") -> Optional[int]:
        """
        Upload a document and return the document ID.

        Args:
            filename: Name of the file to upload from fixtures directory

        Returns:
            Document ID if successful, None otherwise
        """
        pdf_path = LoadTestConfig.SAMPLE_PDF_PATH

        if not pdf_path.exists():
            logger.warning(f"Sample PDF not found: {pdf_path}")
            return None

        try:
            with open(pdf_path, "rb") as f:
                files = {"file": (filename, f, "application/pdf")}
                with self.client.post(
                    LoadTestConfig.DOCUMENTS_CREATE,
                    files=files,
                    headers={"Authorization": self.auth_headers["Authorization"]},
                    catch_response=True,
                    name="[WRITE] Upload Document",
                ) as response:
                    if response.status_code == 201:
                        doc_id = response.json().get("id")
                        response.success()
                        logger.info(f"Document uploaded successfully: ID {doc_id}")
                        return doc_id
                    else:
                        response.failure(
                            f"Failed to upload document: {response.status_code}"
                        )
                        logger.error(f"Upload failed: {response.status_code}")
                        return None
        except Exception as e:
            logger.error(f"Exception during document upload: {e}")
            return None


class ReadHeavyUserTasks(TaskSet):
    """Task set for read-heavy users (60% of load)."""

    @task(4)
    def list_documents(self) -> None:
        """List all documents (most common operation)."""
        self.user.get_document_list()

    @task(3)
    def list_proposals(self) -> None:
        """List all proposals."""
        with self.user.client.get(
            LoadTestConfig.PROPOSALS_LIST,
            headers=self.user.auth_headers,
            catch_response=True,
            name="[READ] List Proposals",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to list proposals: {response.status_code}")

    @task(2)
    def retrieve_document_details(self) -> None:
        """Retrieve details of a specific document."""
        if not self.user.document_ids:
            self.user.get_document_list()

        if self.user.document_ids:
            doc_id = self.user.document_ids[0]
            with self.user.client.get(
                LoadTestConfig.DOCUMENTS_RETRIEVE.format(id=doc_id),
                headers=self.user.auth_headers,
                catch_response=True,
                name="[READ] Retrieve Document Details",
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(
                        f"Failed to retrieve document: {response.status_code}"
                    )

    @task(1)
    def health_check(self) -> None:
        """Check API health (lightweight operation)."""
        with self.user.client.get(
            LoadTestConfig.HEALTH_CHECK,
            catch_response=True,
            name="[HEALTH] OCR Service Status",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class WriteHeavyUserTasks(TaskSet):
    """Task set for write-heavy users (20% of load)."""

    @task(5)
    def upload_document(self) -> None:
        """Upload a document (most common operation)."""
        self.user.upload_document()

    @task(3)
    def process_document(self) -> None:
        """Trigger document processing."""
        if not self.user.document_ids:
            self.user.get_document_list()

        if self.user.document_ids:
            doc_id = self.user.document_ids[0]
            with self.user.client.post(
                LoadTestConfig.DOCUMENTS_PROCESS.format(id=doc_id),
                headers=self.user.auth_headers,
                json={"force_reprocess": False},
                catch_response=True,
                name="[WRITE] Process Document",
            ) as response:
                if response.status_code in [200, 202, 204]:
                    response.success()
                else:
                    response.failure(
                        f"Failed to process document: {response.status_code}"
                    )

    @task(2)
    def check_processing_status(self) -> None:
        """Check the processing status of a document."""
        if not self.user.document_ids:
            self.user.get_document_list()

        if self.user.document_ids:
            doc_id = self.user.document_ids[0]
            with self.user.client.get(
                LoadTestConfig.DOCUMENTS_RETRIEVE.format(id=doc_id),
                headers=self.user.auth_headers,
                catch_response=True,
                name="[READ] Check Processing Status",
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(
                        f"Failed to check status: {response.status_code}"
                    )


class MixedUserTasks(TaskSet):
    """Task set for mixed-usage users (20% of load)."""

    @task(2)
    def list_documents(self) -> None:
        """List documents."""
        self.user.get_document_list()

    @task(2)
    def upload_document(self) -> None:
        """Upload a document."""
        self.user.upload_document()

    @task(1)
    def process_document(self) -> None:
        """Process a document."""
        if not self.user.document_ids:
            self.user.get_document_list()

        if self.user.document_ids:
            doc_id = self.user.document_ids[0]
            with self.user.client.post(
                LoadTestConfig.DOCUMENTS_PROCESS.format(id=doc_id),
                headers=self.user.auth_headers,
                json={"force_reprocess": False},
                catch_response=True,
                name="[WRITE] Process Document (Mixed)",
            ) as response:
                if response.status_code in [200, 202, 204]:
                    response.success()
                else:
                    response.failure(
                        f"Failed to process document: {response.status_code}"
                    )

    @task(1)
    def list_proposals(self) -> None:
        """List proposals."""
        with self.user.client.get(
            LoadTestConfig.PROPOSALS_LIST,
            headers=self.user.auth_headers,
            catch_response=True,
            name="[READ] List Proposals (Mixed)",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to list proposals: {response.status_code}")


class ReadHeavyUser(DraftCraftBaseUser):
    """
    Read-heavy user (60% of total users).

    Simulates users who primarily browse documents and proposals.
    Weight: 3 (out of 5 total weights)
    """

    weight = 3
    tasks = [ReadHeavyUserTasks]


class WriteHeavyUser(DraftCraftBaseUser):
    """
    Write-heavy user (20% of total users).

    Simulates users who primarily upload and process documents.
    Weight: 1 (out of 5 total weights)
    """

    weight = 1
    tasks = [WriteHeavyUserTasks]


class MixedUser(DraftCraftBaseUser):
    """
    Mixed-usage user (20% of total users).

    Simulates users with balanced operations across all endpoints.
    Weight: 1 (out of 5 total weights)
    """

    weight = 1
    tasks = [MixedUserTasks]


# Event handlers for test lifecycle
@events.test_start.add_listener
def on_test_start(environment, **kwargs) -> None:
    """Called when the test starts."""
    logger.info("=" * 70)
    logger.info("LOAD TEST STARTED")
    logger.info("=" * 70)
    logger.info(f"Target host: {environment.host}")
    logger.info(f"Load test configuration loaded successfully")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:
    """Called when the test stops."""
    logger.info("=" * 70)
    logger.info("LOAD TEST COMPLETED")
    logger.info("=" * 70)

    # Print summary statistics
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Failed requests: {stats.total.num_failures}")
    logger.info(f"Success rate: {(1 - stats.total.failure_rate) * 100:.1f}%")
    logger.info(f"Median response time: {stats.total.median_response_time:.0f}ms")
    logger.info(f"95th percentile response time: {stats.total.get_response_time_percentile(0.95):.0f}ms")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs) -> None:
    """Called for each request."""
    if response_time > LoadTestConfig.RESPONSE_TIME_THRESHOLD_MS:
        logger.warning(
            f"Slow request detected: {name} took {response_time:.0f}ms "
            f"(threshold: {LoadTestConfig.RESPONSE_TIME_THRESHOLD_MS}ms)"
        )
