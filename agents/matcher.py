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
        
        # Strong skill matches
        skill_matches = sum(1 for skill in PROFILE["skills"] if skill in text)
        score += skill_matches * 25
        
        # Strong role matches
        if any(role in text for role in PROFILE["preferred_roles"]):
            score += 45
        
        # Flexible / Freelance bonus
        if any(word in text for word in ["freelance", "contract", "part time", "flexible", "remote"]):
            score += 20
        
        # Heavy penalty for unrelated jobs
        bad_keywords = ["courier", "sales", "barista", "driver", "customer success", "athlete", "crypto", "underwriter", "estimator", "executive assistant", "medical records", "project coordinator", "administrative", "virtual assistant"]
        if any(bad in text for bad in bad_keywords):
            score -= 90
        
        return max(0, min(score, 100))

    def rank_jobs(self, jobs: List[Job]) -> List[Job]:
        for job in jobs:
            job.score = self.score_job(job)
        
        jobs = [j for j in jobs if j.score >= 70]
        jobs.sort(key=lambda x: x.score or 0, reverse=True)
        return jobs
