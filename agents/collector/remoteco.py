import requests
from bs4 import BeautifulSoup
from typing import List
from app.models.job import Job

class RemoteCoCollector:
    source = "remoteco"

    def collect(self) -> List[Job]:
        print("🌐 Fetching jobs from Remote.co...")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get("https://remote.co/remote-jobs/", headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            jobs = []
            for card in soup.select('a[href*="/job/"], .job_listing, .job')[:35]:
                title = card.get_text(strip=True)[:100]
                href = card.get('href', '')
                if title and href and len(title) > 10:
                    full_url = href if href.startswith('http') else "https://remote.co" + href
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
            
            print(f"✅ Collected {len(jobs)} jobs from Remote.co")
            return jobs
        except Exception as e:
            print(f"❌ Remote.co failed: {e}")
            return []
