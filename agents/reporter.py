import yaml
from app.services.database import SessionLocal, JobApplication
from datetime import datetime

class Reporter:
    def __init__(self):
        self.profile = self.load_profile()

    def load_profile(self):
        try:
            with open('config/profile.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except:
            return {}

    def generate_daily_report(self):
        session = SessionLocal()
        applications = session.query(JobApplication).order_by(JobApplication.applied_date.desc()).all()
        session.close()

        report = f'CareerPilot Daily Report - {datetime.now().strftime("%B %d, %Y %H:%M")}\n\n'
        report += f'Total Applications Tracked: {len(applications)}\n\n'
        report += 'Recent Applications:\n'
        for app in applications[:15]:
            report += f'• {app.company} | {app.title} | Score: {app.score} | Status: {app.status}\n'
        return report

    def send_daily_report(self):
        report = self.generate_daily_report()
        print(report)
        print('\\n📧 Email sending is currently disabled.')
