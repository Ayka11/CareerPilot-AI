import requests
from bs4 import BeautifulSoup
from typing import List
from app.models.job import Job
from .structured import parse_jsonld

class HimalayasCollector:
    source = "himalayas"

    def collect(self) -> List[Job]:
        print("🌐 Fetching jobs from Himalayas...")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get("https://himalayas.app/jobs", headers=headers, timeout=15)
            resp.raise_for_status()
            structured_jobs = parse_jsonld(resp.text, self.source, "https://himalayas.app", limit=50)
            if structured_jobs:
                print(f"Collected {len(structured_jobs)} jobs from Himalayas")
                return structured_jobs
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            jobs = []
            for card in soup.select('a[href*="/jobs/"]')[:30]:
                title = card.get_text(strip=True)
                href = card.get('href', '')
                if title and href and len(title) > 5:
                    job = Job(
                        company="Unknown",
                        title=title[:100],
                        url="https://himalayas.app" + href if href.startswith('/') else href,
                        remote=True,
                        description="",
                        skills=[],
                        source=self.source
                    )
                    jobs.append(job)
            
            print(f"✅ Collected {len(jobs)} jobs from Himalayas")
            return jobs
        except Exception as e:
            print(f"❌ Himalayas failed: {e}")
            return []
