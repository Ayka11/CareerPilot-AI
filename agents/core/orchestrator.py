from typing import List
import webbrowser
from agents.collector.manager import CollectorManager
from agents.matcher import JobMatcher
from agents.resume import ResumeBuilder
from agents.coverletter import CoverLetterBuilder
from agents.reporter import Reporter
from app.services.database import init_db
from app.models.job import Job
import yaml

class CareerPilotAgent:
    def __init__(self):
        self.profile = self.load_profile()
        self.collector = CollectorManager(target_regions=self.profile.get('target_regions'))
        self.matcher = JobMatcher()
        self.resume_builder = ResumeBuilder()
        self.coverletter_builder = CoverLetterBuilder()
        self.reporter = Reporter()
        init_db()

    def load_profile(self):
        try:
            with open('config/profile.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except:
            return {}

    def run_daily(self, top_n: int = 15):
        print('CAREERPILOT AGENT - DAILY RUN STARTED')

        jobs = self.collector.collect_all()
        ranked = self.matcher.rank_jobs(jobs)
        fresh = self._drop_already_seen(ranked)
        selected = self._select_diverse_jobs(fresh, top_n)

        print(f'\nTop {len(selected)} matched jobs (opening links):\n')

        opened = 0
        for i, job in enumerate(selected, 1):
            print(f'{i}. {job.score}% | {job.company} | {job.title}')
            
            self.resume_builder.generate_for_job(job)
            self.coverletter_builder.generate_for_job(job)
            self.track_application(job)
            
            if job.url:
                url_str = str(job.url)
                try:
                    webbrowser.open(url_str)
                    print(f'   🌐 Opened: {url_str[:70]}...')
                    opened += 1
                except Exception as e:
                    print(f'   ⚠️ Could not open link: {e}')

        self.reporter.send_daily_report()

        print(f'\nDAILY RUN COMPLETED SUCCESSFULLY (opened {opened} jobs)')
        return selected

    @staticmethod
    def _drop_already_seen(ranked: List[Job]) -> List[Job]:
        """Filter out jobs whose URL is already recorded from a prior run."""
        from app.services.database import SessionLocal, JobApplication

        session = SessionLocal()
        try:
            seen_urls = {row[0] for row in session.query(JobApplication.job_url).all()}
        finally:
            session.close()

        return [job for job in ranked if str(job.url) not in seen_urls]

    @staticmethod
    def _select_diverse_jobs(ranked: List[Job], top_n: int) -> List[Job]:
        """Keep the best results while preventing one source from dominating."""
        if top_n <= 0:
            return []

        by_source = {}
        for job in ranked:
            by_source.setdefault(getattr(job, 'source', 'unknown'), []).append(job)

        selected = []
        source_names = list(by_source)
        while len(selected) < top_n and source_names:
            remaining_sources = []
            for source in source_names:
                jobs = by_source[source]
                if jobs:
                    selected.append(jobs.pop(0))
                if jobs:
                    remaining_sources.append(source)
                if len(selected) >= top_n:
                    break
            source_names = remaining_sources
        return selected

    def track_application(self, job):
        from app.services.database import SessionLocal, JobApplication
        session = SessionLocal()
        try:
            app = JobApplication(
                job_url=str(job.url),
                company=job.company,
                title=job.title,
                score=job.score
            )
            session.add(app)
            session.commit()
        except:
            session.rollback()
        finally:
            session.close()
