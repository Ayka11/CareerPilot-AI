from rich import print
from agents.collector.manager import CollectorManager
from agents.matcher import JobMatcher  # improve this too
from app.services.database import init_db

def main():
    print("[bold green]CareerPilot Agent[/bold green]")
    init_db()

    manager = CollectorManager()
    jobs = manager.collect_all()
    manager.save_to_db(jobs)

    matcher = JobMatcher()
    ranked = matcher.rank_jobs(jobs)

    print(f"\nFound {len(ranked)} unique jobs.\n")
    for job in ranked[:20]:
        print(f"{job.score or 0:>3}% | {job.company} | {job.title}")

if __name__ == "__main__":
    main()
