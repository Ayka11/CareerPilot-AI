import requests
from bs4 import BeautifulSoup
from typing import List
from app.models.job import Job
from .structured import parse_jsonld

class JustRemoteCollector:
    source = "justremote"

    def collect(self) -> List[Job]:
        print("🌐 Fetching jobs from JustRemote...")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get("https://justremote.co/remote-jobs", headers=headers, timeout=15)
            resp.raise_for_status()
            structured_jobs = parse_jsonld(resp.text, self.source, "https://justremote.co", limit=50)
            if structured_jobs:
                print(f"Collected {len(structured_jobs)} jobs from JustRemote")
                return structured_jobs
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            jobs = []
            for card in soup.select('a[href*="/remote-jobs/"], .job')[:25]:
                title = card.get_text(strip=True)[:90]
                href = card.get('href', '')
                if title and href and len(title) > 8:
                    full_url = href if href.startswith('http') else "https://justremote.co" + href
                    job = Job(
                        company="Unknown",
                        title=title,
                        url=full_url,
                        remote=True,
                        description="",
                        skills=[],
                        source=self.source
                    )
                    jobs.append(job)
            
            print(f"✅ Collected {len(jobs)} jobs from JustRemote")
            return jobs
        except Exception as e:
            print(f"❌ JustRemote failed: {e}")
            return []
