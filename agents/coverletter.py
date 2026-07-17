import yaml
from pathlib import Path
from app.models.job import Job
from datetime import datetime
import re

class CoverLetterBuilder:
    def __init__(self):
        self.profile = self.load_profile()

    def load_profile(self):
        try:
            with open('config/profile.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except:
            return {'name': 'Aygun Aliyeva'}

    def generate_for_job(self, job: Job, output_dir: str = 'outputs/coverletters') -> str:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        content = f'''
{self.profile.get('name', 'Aygun Aliyeva')}
{self.profile.get('email')} | {self.profile.get('phone')} | Remote

{datetime.now().strftime('%B %d, %Y')}

Hiring Manager
{job.company}

Dear Hiring Manager,

I am excited to apply for the {job.title} position at {job.company}.

With my background in technical writing, content creation, research and project management, I believe I would be a strong fit for your team.

I would welcome the opportunity to discuss how my skills can contribute to {job.company}.

Sincerely,
Aygun Aliyeva
'''

        safe_company = ''.join(e for e in job.company if e.isalnum() or e in (' ', '-', '_'))[:50]
        filename = f'{output_dir}/coverletter_{safe_company}_{datetime.now().strftime("%Y%m%d")}.txt'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        
        print(f'   📄 Cover letter generated for {job.company}')
        return filename
