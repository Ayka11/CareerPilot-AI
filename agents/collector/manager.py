from typing import List
from .linkedin import LinkedInCollector
from .weworkremotely import WeWorkRemotelyCollector
from .jobspresso import JobspressoCollector
from .workingnomads import WorkingNomadsCollector
from .remotive import RemotiveCollector
from .himalayas import HimalayasCollector
from .jobicy import JobicyCollector
from .justremote import JustRemoteCollector
from .trulyremote import TrulyRemoteCollector
from .remoteco import RemoteCoCollector
from app.models.job import Job

class CollectorManager:
    def __init__(self):
        self.collectors = [
            LinkedInCollector(),
            HimalayasCollector(),
            JobicyCollector(),
            TrulyRemoteCollector(),
            JustRemoteCollector(),
            RemoteCoCollector(),
            WeWorkRemotelyCollector(),
            RemotiveCollector(),
            JobspressoCollector(),
            WorkingNomadsCollector()
        ]

    def collect_all(self) -> List[Job]:
        all_jobs = []
        for collector in self.collectors:
            try:
                jobs = collector.collect()
                print(f"{collector.source}: {len(jobs)} jobs before per-source cap")
                all_jobs.extend(jobs[:20])
            except Exception as e:
                print(f"{getattr(collector, 'source', 'unknown')} failed: {e}")
        
        filtered = self.filter_good_jobs(all_jobs)
        return filtered

    def filter_good_jobs(self, jobs: List[Job]) -> List[Job]:
        good_jobs = []
        bad_keywords = ['commission', 'mlm', 'relocation', 'onsite', 'in-office', 'citizenship', 'sales manager', 'barista', 'driver']
        
        seen = set()
        for job in jobs:
            key = (job.company.lower().strip(), job.title.lower().strip())
            if key in seen:
                continue
            seen.add(key)
            
            text = (job.title + " " + (job.description or "")).lower()
            
            if not getattr(job, 'remote', True):
                continue
            if any(bad in text for bad in bad_keywords):
                continue
                
            good_jobs.append(job)
        
        print(f'✅ After filtering: {len(good_jobs)} good jobs from all sources')
        return good_jobs
