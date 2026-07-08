import requests
from typing import List, Dict

def collect_remoteok() -> List[Dict]:
    """Collect real jobs from RemoteOK"""
    try:
        headers = {"User-Agent": "CareerPilot-Agent"}
        response = requests.get("https://remoteok.com/api", headers=headers, timeout=15)
        response.raise_for_status()
        
        jobs = response.json()[1:]  # Skip the first info item
        
        clean_jobs = []
        for job in jobs[:30]:   # Limit to 30 for now
            clean_jobs.append({
                "company": job.get("company", "Unknown"),
                "title": job.get("position", "No Title"),
                "url": f"https://remoteok.com/remote-jobs/{job.get('slug')}",
                "remote": True,
                "hours": "Full-time",  # Most are full-time
                "skills": job.get("tags", []),
                "description": job.get("description", "")[:500]
            })
        return clean_jobs
        
    except Exception as e:
        print(f"❌ RemoteOK failed: {e}")
        return []
