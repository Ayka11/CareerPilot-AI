import requests
from bs4 import BeautifulSoup
from typing import List
from app.models.job import Job

class JobicyCollector:
    source = "jobicy"

    def collect(self) -> List[Job]:
        print("🌐 Fetching jobs from Jobicy...")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get("https://jobicy.com/remote-jobs", headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            jobs = []
            for card in soup.select('a[href*="/job/"], .job-card, .job')[:30]:
                title = card.get_text(strip=True)[:90]
                href = card.get('href', '')
                if title and href and len(title) > 8:
                    full_url = href if href.startswith('http') else "https://jobicy.com" + href
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
            
            print(f"✅ Collected {len(jobs)} jobs from Jobicy")
            return jobs
        except Exception as e:
            print(f"❌ Jobicy failed: {e}")
            return []
