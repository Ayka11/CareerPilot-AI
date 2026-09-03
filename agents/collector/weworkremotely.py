import requests
from bs4 import BeautifulSoup
from typing import List
from app.models.job import Job
from .structured import parse_feed

class WeWorkRemotelyCollector:
    source = "weworkremotely"

    def collect(self) -> List[Job]:
        print("Fetching jobs from We Work Remotely RSS...")
        try:
            categories = (
                "all-other-remote-jobs",
                "remote-sales-and-marketing-jobs",
                "remote-product-jobs",
                "remote-back-end-programming-jobs",
            )
            jobs = []
            for category in categories:
                jobs.extend(parse_feed(
                    f"https://weworkremotely.com/categories/{category}.rss",
                    self.source,
                    limit=20,
                ))
            unique = {}
            for job in jobs:
                unique.setdefault(str(job.url), job)
            jobs = list(unique.values())[:50]
            print(f"Collected {len(jobs)} jobs from We Work Remotely")
            return jobs
        except Exception as e:
            print(f"We Work Remotely failed: {e}")
            return []
