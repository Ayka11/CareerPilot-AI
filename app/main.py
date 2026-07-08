# app/main.py
from rich import print

# New import path
from agents.collector.manager import CollectorManager

def main():
    print("[bold green]CareerPilot AI[/bold green]")

    # Collect real jobs
    manager = CollectorManager()
    jobs = manager.collect_all()

    print(f"\nFound {len(jobs)} jobs from real sources.\n")

    # Show top jobs
    for job in jobs[:20]:
        score = getattr(job, 'score', 0)
        print(f"{score:>3}% | {job.company} | {job.title}")

if __name__ == "__main__":
    main()
