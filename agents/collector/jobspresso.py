import requests
from bs4 import BeautifulSoup
from typing import List
from app.models.job import Job
from .structured import parse_jsonld

class JobspressoCollector:
    source = "jobspresso"

    def collect(self) -> List[Job]:
        print("Fetching jobs from Jobspresso structured data...")
        try:
            response = requests.get(
                "https://jobspresso.co/remote-jobs/",
                headers={"User-Agent": "CareerPilot-AI/1.0"},
                timeout=20,
            )
            response.raise_for_status()
            jobs = parse_jsonld(
                response.text,
                self.source,
                "https://jobspresso.co/remote-jobs/",
                limit=50,
            )
            print(f"Collected {len(jobs)} jobs from Jobspresso")
            return jobs
        except Exception as e:
            print(f"Jobspresso failed: {e}")
            return []
