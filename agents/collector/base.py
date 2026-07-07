from abc import ABC, abstractmethod
from typing import List
from app.models.job import Job

class BaseCollector(ABC):
    source: str

    @abstractmethod
    def collect(self) -> List[Job]:
        pass

    def normalize(self, raw_job: dict) -> Job:
        """Convert raw data to Job model with defaults/validation"""
        return Job(
            company=raw_job.get("company", "Unknown"),
            title=raw_job.get("title", ""),
            url=raw_job["url"],
            # ... map other fields
            source=self.source
        )
