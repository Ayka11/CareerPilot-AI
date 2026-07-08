import sys
import os

# Fix Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from remoteok import collect_remoteok

class JobCollector:
    def collect(self):
        """Collect real jobs from RemoteOK"""
        print("🌐 Fetching jobs from RemoteOK...")
        
        jobs = collect_remoteok()
        
        if not jobs:
            print("⚠️  Failed to fetch jobs, using mock data")
            return [
                {
                    "company": "Example Company",
                    "title": "Technical Writer",
                    "remote": True,
                    "hours": "Flexible",
                    "skills": ["python", "writing"]
                }
            ]
        
        print(f"✅ Successfully collected {len(jobs)} real jobs!")
        return jobs
