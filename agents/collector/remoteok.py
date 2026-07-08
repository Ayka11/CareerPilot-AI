import requests
from typing import List, Dict

def collect_remoteok() -> List[Dict]:
    print("🌐 Fetching jobs from RemoteOK...")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; CareerPilot/1.0)"}
        resp = requests.get("https://remoteok.com/api", headers=headers, timeout=20)
        resp.raise_for_status()
        
        data = resp.json()[1:]  # Skip first item
        
        jobs = []
        for item in data[:40]:
            jobs.append({
                "company": item.get("company", "Unknown Company"),
                "title": item.get("position", "Untitled Position"),
                "url": f"https://remoteok.com/remote-jobs/{item.get('slug')}",
                "remote": True,
                "hours": "Flexible",
                "skills": [tag.lower() for tag in item.get("tags", [])],
                "description": item.get("description", "")
            })
        print(f"✅ Successfully fetched {len(jobs)} jobs from RemoteOK")
        return jobs
        
    except Exception as e:
        print(f"❌ Failed to fetch from RemoteOK: {e}")
        return []
