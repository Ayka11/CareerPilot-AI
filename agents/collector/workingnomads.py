import requests
from bs4 import BeautifulSoup
from typing import List
from app.models.job import Job

class WorkingNomadsCollector:
    source = "workingnomads"

    def collect(self) -> List[Job]:
        print("🌐 Fetching jobs from Working Nomads...")
        try:
            resp = requests.get("https://www.workingnomads.com/jobs", headers={"User-Agent": "CareerPilot-Agent"})
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            jobs = []
            for job in soup.select('.job')[:20]:
                title = job.select_one('h2')
                company = job.select_one('.company')
                link = job.select_one('a')
                
                if title and link:
                    job_obj = Job(
                        company=company.get_text(strip=True) if company else "Unknown",
                        title=title.get_text(strip=True),
                        url=link.get('href', ''),
                        remote=True,
                        description="",
                        skills=[],
                        source=self.source
                    )
                    jobs.append(job_obj)
            
            print(f"✅ Collected {len(jobs)} jobs from Working Nomads")
            return jobs
        except Exception as e:
            print(f"❌ Working Nomads failed: {e}")
            return []
