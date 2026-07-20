import requests
from bs4 import BeautifulSoup
from typing import List
from app.models.job import Job

class LinkedInCollector:
    source = "linkedin"

    def collect(self) -> List[Job]:
        print("🌐 Fetching jobs from LinkedIn...")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; CareerPilot/1.0)"}
            
            # Broader set of search terms
            search_terms = [
                "technical writer",
                "content writer",
                "researcher",
                "documentation specialist",
                "copywriter",
                "content strategist",
                "technical documentation"
            ]
            
            jobs = []
            for term in search_terms:
                url = f"https://www.linkedin.com/jobs/search?keywords={term.replace(' ', '%20')}&location=Worldwide&f_WT=2"  # Remote only
                resp = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                for card in soup.select('.base-card')[:5]:  # Limit per term
                    title = card.select_one('h3')
                    company = card.select_one('.base-search-card__subtitle')
                    link = card.select_one('a')
                    
                    if title and link:
                        job = Job(
                            company=company.get_text(strip=True) if company else "Unknown",
                            title=title.get_text(strip=True),
                            url=link.get('href', ''),
                            remote=True,
                            description="",
                            skills=[],
                            source=self.source
                        )
                        jobs.append(job)
            
            print(f"✅ Collected {len(jobs)} jobs from LinkedIn")
            return jobs
        except Exception as e:
            print(f"❌ LinkedIn failed: {e}")
            return []
