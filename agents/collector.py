import sys
import os

# Fix import path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from remoteok import collect_remoteok

class JobCollector:
    def collect(self):
        """Collect real jobs from RemoteOK"""
        print("🌐 Collecting real jobs from RemoteOK...")
        
        jobs = collect_remoteok()
        
        if not jobs:
            print("⚠️  No jobs fetched, using mock data")
            return [
                {
                    "company": "Example Company",
                    "title": "Technical Writer",
                    "remote": True,
                    "hours": "Flexible",
                    "skills": ["python", "documentation", "writing"]
                }
            ]
        
        print(f"✅ Loaded {len(jobs)} real jobs")
        return jobs
