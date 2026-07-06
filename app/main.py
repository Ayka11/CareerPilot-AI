from rich import print

from agents.collector import JobCollector
from agents.matcher import JobMatcher


def main():

    print("[bold green]CareerPilot AI[/bold green]")

    collector = JobCollector()

    jobs = collector.collect()

    matcher = JobMatcher()

    ranked = matcher.rank_jobs(jobs)

    print(f"\nFound {len(ranked)} jobs.\n")

    for job in ranked:

        print(
            f"{job['score']:>3}% | "
            f"{job['company']} | "
            f"{job['title']}"
        )


if __name__ == "__main__":
    main()
