from .remoteok import collect_remoteok

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
                }
            ]
        return jobs
