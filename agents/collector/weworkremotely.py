import requests
from bs4 import BeautifulSoup
from typing import List
from app.models.job import Job

class WeWorkRemotelyCollector:
    source = "weworkremotely"

    def collect(self) -> List[Job]:
        print("🌐 Fetching jobs from We Work Remotely...")
        try:
            resp = requests.get("https://weworkremotely.com/remote-jobs", headers={"User-Agent": "CareerPilot-Agent"})
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            jobs = []
            for job in soup.select('.job')[:25]:
                title = job.select_one('.title')
                company = job.select_one('.company')
                link = job.select_one('a')
                
                if title and link:
                    job_obj = Job(
                        company=company.get_text(strip=True) if company else "Unknown",
                        title=title.get_text(strip=True),
                        url="https://weworkremotely.com" + link.get('href', ''),
                        remote=True,
                        description="",
                        skills=[],
                        source=self.source
                    )
                    jobs.append(job_obj)
            
            print(f"✅ Collected {len(jobs)} jobs from We Work Remotely")
            return jobs
        except Exception as e:
            print(f"❌ We Work Remotely failed: {e}")
            return []
