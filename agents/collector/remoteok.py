import requests
from typing import List
from app.models.job import Job   # We'll create this model next if missing

class RemoteOKCollector:
    def collect(self) -> List[Job]:
        try:
            resp = requests.get(
                "https://remoteok.com/api",
                headers={"User-Agent": "CareerPilot-Agent"}
            )
            resp.raise_for_status()
            data = resp.json()[1:]  # Skip header row

            jobs = []
            for item in data[:50]:
                job = Job(
                    company=item.get("company", "Unknown"),
                    title=item.get("position", ""),
                    url=f"https://remoteok.com/remote-jobs/{item.get('slug')}",
                    salary=item.get("salary"),
                    remote=True,
                    description=item.get("description"),
                    skills=item.get("tags", []),
                    source="remoteok"
                )
                jobs.append(job)
            print(f"✅ Collected {len(jobs)} jobs from RemoteOK")
            return jobs
        except Exception as e:
            print(f"❌ RemoteOK collection failed: {e}")
            return []
