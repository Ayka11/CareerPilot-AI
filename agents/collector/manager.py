from typing import List
from .linkedin import LinkedInCollector
from app.models.job import Job

class CollectorManager:
    def __init__(self):
        self.collectors = [
            LinkedInCollector()
        ]

    def collect_all(self) -> List[Job]:
        all_jobs = []
        for collector in self.collectors:
            jobs = collector.collect()
            all_jobs.extend(jobs)
        
        filtered = self.filter_good_jobs(all_jobs)
        return filtered

    def filter_good_jobs(self, jobs: List[Job]) -> List[Job]:
        good_jobs = []
        bad_keywords = ['commission', 'mlm', 'relocation', 'onsite', 'in-office', 'citizenship', 'sales manager', 'barista', 'driver']
        
        for job in jobs:
            text = (job.title + " " + (job.description or "")).lower()
            
            if not job.remote:
                continue
            if any(bad in text for bad in bad_keywords):
                continue
                
            good_jobs.append(job)
        
        print(f'✅ After filtering: {len(good_jobs)} good jobs from LinkedIn')
        return good_jobs
