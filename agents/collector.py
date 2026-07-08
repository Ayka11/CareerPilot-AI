# Fixed version without relative import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from agents.collector.remoteok import collect_remoteok
except ImportError:
    from remoteok import collect_remoteok

class JobCollector:
    def collect(self):
        """Collect real jobs"""
        print("🔍 Collecting jobs...")
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
