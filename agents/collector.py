import sys
import os

# Fix import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from remoteok import collect_remoteok

class JobCollector:
    def collect(self):
        """Collect real jobs from RemoteOK"""
        print("🌐 Fetching jobs from RemoteOK...")
        
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
        print(f"✅ Successfully collected {len(jobs)} real jobs!")
        return jobs
