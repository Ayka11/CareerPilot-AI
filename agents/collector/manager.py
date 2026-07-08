# agents/collector/manager.py
from typing import List
from .remoteok import RemoteOKCollector
from app.models.job import Job

class CollectorManager:
    def __init__(self):
        self.collectors = [
            RemoteOKCollector(),
            # Add RemotiveCollector() later
        ]

    def collect_all(self) -> List[Job]:
        all_jobs = []
        for collector in self.collectors:
            try:
                jobs = collector.collect()
                all_jobs.extend(jobs)
                print(f"✅ Collected {len(jobs)} jobs from {collector.source}")
            except Exception as e:
                print(f"❌ {collector.source} failed: {e}")

        # Simple deduplication by URL
        seen = {}
        unique_jobs = []
        for job in all_jobs:
            if job.url not in seen:
                seen[job.url] = True
                unique_jobs.append(job)

        print(f"📊 Total unique jobs: {len(unique_jobs)}")
        return unique_jobs
