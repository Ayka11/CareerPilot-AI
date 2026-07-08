from typing import List, Dict
from .collector.remoteok import RemoteOKCollector

class JobCollector:
    def collect(self):
        """Collect real jobs"""
        try:
            collector = RemoteOKCollector()
            jobs = collector.collect()
            return [job.model_dump() for job in jobs]   # convert Pydantic to dict for now
        except Exception as e:
            print(f"⚠️ Collector error: {e}. Using fallback mock data.")
            return [
                {
                    "company": "Example Company",
                    "title": "Technical Writer",
                    "remote": True,
                    "hours": "Flexible",
                    "skills": ["python", "documentation", "writing"]
                }
            ]
