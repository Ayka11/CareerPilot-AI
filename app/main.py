from rich import print

# Simple version that works with current code
from agents.collector import JobCollector
from agents.matcher import JobMatcher


def main():
    print("[bold green]CareerPilot AI[/bold green]")

    collector = JobCollector()
    jobs = collector.collect()

    matcher = JobMatcher()
    ranked = matcher.rank_jobs(jobs)

    print(f"\nFound {len(ranked)} jobs.\n")

    for job in ranked[:15]:   # Show top 15
        score = job.get('score', 0)
        company = job.get('company', 'N/A')
        title = job.get('title', 'N/A')
        print(f"{score:>3}% | {company} | {title}")


if __name__ == "__main__":
    main()
