from typing import List
import webbrowser
from agents.collector.manager import CollectorManager
from agents.matcher import JobMatcher
from agents.resume import ResumeBuilder
from agents.coverletter import CoverLetterBuilder
from agents.reporter import Reporter
from app.services.database import init_db
import yaml

class CareerPilotAgent:
    def __init__(self):
        self.collector = CollectorManager()
        self.matcher = JobMatcher()
        self.resume_builder = ResumeBuilder()
        self.coverletter_builder = CoverLetterBuilder()
        self.reporter = Reporter()
        self.profile = self.load_profile()
        init_db()

    def load_profile(self):
        try:
            with open('config/profile.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except:
            return {}

    def run_daily(self, top_n: int = 5):
        print('CAREERPILOT AGENT - DAILY RUN STARTED')

        jobs = self.collector.collect_all()
        ranked = self.matcher.rank_jobs(jobs)

        print(f'\nTop {top_n} matched jobs (opening links):\n')

        for i, job in enumerate(ranked[:top_n], 1):
            print(f'{i}. {job.score}% | {job.company} | {job.title}')
            
            self.resume_builder.generate_for_job(job)
            self.coverletter_builder.generate_for_job(job)
            self.track_application(job)
            
            # Auto open job link
            if hasattr(job, 'url') and job.url:
                try:
                    webbrowser.open(str(job.url))
                    print(f'   🌐 Opened job link')
                except:
                    print(f'   ⚠️ Could not open link')

        self.reporter.send_daily_report()

        print('\nDAILY RUN COMPLETED SUCCESSFULLY')
        return ranked[:top_n]

    def track_application(self, job):
        from app.services.database import SessionLocal, JobApplication
        session = SessionLocal()
        try:
            existing = session.query(JobApplication).filter_by(job_url=str(job.url)).first()
            if existing:
                existing.score = job.score
            else:
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
