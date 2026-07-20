import requests
from typing import List
from app.models.job import Job

class RemotiveCollector:
    source = "remotive"

    def collect(self) -> List[Job]:
        print("🌐 Fetching jobs from Remotive...")
        try:
            resp = requests.get("https://remotive.com/api/remote-jobs")
            data = resp.json().get("jobs", [])[:30]

            jobs = []
            for item in data:
                job = Job(
                    company=item.get("company_name", "Unknown"),
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    salary=item.get("salary", ""),
                    remote=True,
                    description=item.get("description", ""),
                    skills=[],
                    source=self.source
                )
                jobs.append(job)
            print(f"✅ Collected {len(jobs)} jobs from Remotive")
            return jobs
        except Exception as e:
            print(f"❌ Remotive failed: {e}")
            return []
