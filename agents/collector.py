# agents/collector.py
from typing import List, Dict

def collect_remoteok() -> List[Dict]:
    """Temporary bridge until full manager is ready"""
    try:
        # Try to import from the subpackage
        from .collector.remoteok import RemoteOKCollector
        collector = RemoteOKCollector()
        jobs = collector.collect()
        return [job.model_dump() for job in jobs if hasattr(job, 'model_dump')]
    except Exception as e:
        print(f"⚠️ Real collector not ready yet: {e}")
        return []


class JobCollector:
    def collect(self):
        """Main collection method"""
        jobs = collect_remoteok()
        
        if not jobs:
            print("⚠️ Using fallback mock data")
            return [
                {
                    "company": "Example Company",
                    "title": "Technical Writer",
                    "remote": True,
                    "hours": "Flexible",
                    "skills": ["python", "documentation", "writing"]
                },
                {
                    "company": "Example Startup",
                    "title": "Research Assistant",
                    "remote": True,
                    "hours": "Part-time",
                    "skills": ["research", "writing"]
                }
            ]
        return jobs
