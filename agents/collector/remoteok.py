import requests
from typing import List
from app.models.job import Job

class RemoteOKCollector:
    source = "remoteok"

    def collect(self) -> List[Job]:
        print("🌐 Fetching jobs from RemoteOK...")
        try:
            resp = requests.get("https://remoteok.com/api", headers={"User-Agent": "CareerPilot-Agent"})
            resp.raise_for_status()
            data = resp.json()[1:]

            jobs = []
            for item in data[:50]:
                try:
                    job = Job(
                        company=item.get("company", "Unknown"),
                        title=item.get("position", "No Title"),
                        url=f"https://remoteok.com/remote-jobs/{item.get('slug')}",
                        salary=item.get("salary"),
                        remote=True,
                        description=item.get("description"),
                        skills=item.get("tags", []),
                        source=self.source
                    )
                    jobs.append(job)
                except:
                    continue
            print(f"✅ Collected {len(jobs)} jobs from RemoteOK")
            return jobs
        except Exception as e:
            print(f"❌ RemoteOK failed: {e}")
            return []
