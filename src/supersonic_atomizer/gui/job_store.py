"""In-memory simulation job store for the FastAPI GUI layer (P25-T03).

Each simulation run is assigned a UUID job_id.  The running thread stores
its result (or error) here when finished.  The browser polls the status
endpoint until the job is complete, then fetches the result endpoint.

Thread-safety: all public methods acquire the internal lock.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from supersonic_atomizer.app.services import SimulationRunResult


@dataclass
class JobRecord:
    job_id: str
    status: str = "running"           # "running" | "completed" | "failed"
    result: Optional[Any] = None
    error: Optional[str] = None


class JobStore:
    """Thread-safe in-memory store for simulation job records."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = threading.Lock()

    def create_job(self) -> str:
        """Create a new job in 'running' state and return its job_id."""
        job_id = str(uuid.uuid4())
        with self._lock:
            self._jobs[job_id] = JobRecord(job_id=job_id)
        return job_id

    def mark_complete(self, job_id: str, result: Any) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is not None:
                record.status = "completed"
                record.result = result

    def mark_failed(self, job_id: str, error: str) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is not None:
                record.status = "failed"
                record.error = error

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)

    def all_ids(self) -> list[str]:
        with self._lock:
            return list(self._jobs.keys())


# Module-level singleton — one store per server process.
_job_store = JobStore()


def get_job_store() -> JobStore:
    """Return the module-level JobStore singleton."""
    return _job_store
