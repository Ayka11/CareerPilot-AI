from typing import List
from .remoteok import RemoteOKCollector
from .remotive import RemotiveCollector  # implement similarly
from app.services.database import SessionLocal, JobDB
from app.models.job import Job

class CollectorManager:
    def __init__(self):
        self.collectors = [RemoteOKCollector()]  # add more

    def collect_all(self) -> List[Job]:
        all_jobs = []
        for collector in self.collectors:
            jobs = collector.collect()
            all_jobs.extend(jobs)
        return self.deduplicate(all_jobs)

    def deduplicate(self, jobs: List[Job]) -> List[Job]:
        seen = set()
        unique = []
        for job in jobs:
            if job.url not in seen:
                seen.add(job.url)
                unique.append(job)
        return unique

    def save_to_db(self, jobs: List[Job]):
        session = SessionLocal()
        for job in jobs:
            db_job = JobDB(**job.model_dump(exclude={"id"}))
            session.merge(db_job)  # upsert by unique url
        session.commit()
        session.close()
