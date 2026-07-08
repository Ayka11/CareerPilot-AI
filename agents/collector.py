# agents/collector.py
from typing import List, Dict

def collect_remoteok() -> List[Dict]:
    """Placeholder until we create the real collector"""
    try:
        # We'll implement this properly soon
        from agents.collector.remoteok import RemoteOKCollector
        collector = RemoteOKCollector()
        return [job.model_dump() for job in collector.collect()]
    except Exception:
        print("⚠️ RemoteOK collector not ready yet")
        return []


class JobCollector:
    def collect(self):
        """Collect real jobs"""
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
