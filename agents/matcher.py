from typing import List
from app.models.job import Job

PROFILE = {
    "skills": ["technical writing", "content writing", "research", "documentation", "copywriting", "seo", "content strategy", "editing", "translation"],
    "preferred_roles": ["technical writer", "content writer", "writer", "researcher", "documentation", "copywriter", "content strategist"]
}

class JobMatcher:
    def score_job(self, job: Job) -> int:
        score = 40
        text = (job.title + " " + (job.description or "")).lower()
        
        skill_matches = sum(1 for skill in PROFILE["skills"] if skill in text)
        score += skill_matches * 22
        
        if any(role in text for role in PROFILE["preferred_roles"]):
            score += 35
            
        if any(word in text for word in ["freelance", "contract", "part time", "flexible", "remote"]):
            score += 18
            
        # Penalty for bad jobs
        bad = ["courier", "sales", "barista", "driver", "customer success", "athlete", "crypto", "underwriter", "estimator", "medical records", "executive assistant"]
        if any(word in text for word in bad):
            score -= 60
        
        return max(0, min(score, 100))

    def rank_jobs(self, jobs: List[Job]) -> List[Job]:
        for job in jobs:
            job.score = self.score_job(job)
        
        # Sort all jobs, but guarantee at least 5 if available
        jobs.sort(key=lambda x: x.score or 0, reverse=True)
        
        # Take top 5 (or all if less than 5)
        return jobs[:5]
