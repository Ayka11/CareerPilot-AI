from .remoteok import collect_remoteok

class JobCollector:
    def collect(self):
        print("Collecting real jobs from RemoteOK...")
        jobs = collect_remoteok()
        
        if not jobs:
            print("⚠️  Falling back to mock data")
            return [
                {"company": "Example Company", "title": "Technical Writer", "remote": True, "hours": "Flexible", "skills": ["python", "writing"]},
            ]
        
        print(f"✅ Collected {len(jobs)} real jobs")
        return jobs
