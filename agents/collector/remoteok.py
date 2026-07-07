import requests
from typing import List
from .base import BaseCollector
from app.models.job import Job

class RemoteOKCollector(BaseCollector):
    source = "remoteok"
    url = "https://remoteok.com/api"

    def collect(self) -> List[Job]:
        try:
            resp = requests.get(self.url, headers={"User-Agent": "CareerPilot-Agent"})
            resp.raise_for_status()
            data = resp.json()[1:]  # skip first header item

            jobs = []
            for item in data[:50]:  # limit for now
                job = self.normalize({
                    "company": item.get("company"),
                    "title": item.get("position"),
                    "url": f"https://remoteok.com/remote-jobs/{item.get('slug')}",
                    "salary": item.get("salary"),
                    "location": item.get("location"),
                    "remote": True,  # RemoteOK is mostly remote
                    "description": item.get("description"),
                    "skills": item.get("tags", []),
                })
                jobs.append(job)
            return jobs
        except Exception as e:
            print(f"RemoteOK error: {e}")
            return []
