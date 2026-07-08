# app/main.py
from rich import print

from agents.collector.manager import CollectorManager

def main():
    print("[bold green]CareerPilot AI[/bold green]")

    manager = CollectorManager()
    jobs = manager.collect_all()

    print(f"\nFound {len(jobs)} jobs.\n")

    for job in jobs[:15]:
        score = getattr(job, 'score', 0)
        print(f"{score:>3}% | {job.company} | {job.title}")

if __name__ == "__main__":
    main()
