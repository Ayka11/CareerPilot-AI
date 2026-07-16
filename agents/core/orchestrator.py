"""
CareerPilot orchestrator — cross-platform entry point.

Run with:  python -m agents.core.orchestrator
or via the console script:  careerpilot

Pipeline:
    collect -> dedup -> match/rank -> record (tracker)
            -> generate cover letter -> attach docs -> open link -> report

The tracker keeps every surfaced job at status FOUND. You flip a job to APPLIED
yourself (via view_tracked.py) once you've actually submitted — the human stays
in the loop for submission. Auto-*opening* links is fine; auto-*submitting* is
intentionally not done.
"""

from __future__ import annotations

import logging
import os
import webbrowser
from pathlib import Path

logger = logging.getLogger("careerpilot")


def _load_env() -> None:
    """Load .env if python-dotenv is installed (optional dependency)."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        logger.debug("python-dotenv not installed; relying on real env vars")


def _load_profile() -> dict:
    import yaml

    path = Path("config/profile.yaml")
    if not path.exists():
        raise FileNotFoundError(
            "config/profile.yaml not found. Copy config/profile.example.yaml "
            "to config/profile.yaml and fill it in."
        )
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _job_field(job, key, default=""):
    val = job.get(key, default) if isinstance(job, dict) else getattr(job, key, default)
    return default if val is None else val


def run() -> list:
    _load_env()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    profile = _load_profile()
    sources = profile.get("sources") or ["remotive", "remoteok"]
    query = " ".join(profile.get("target_roles", [])) or ""
    top_k = int(os.getenv("TOP_K_JOBS", "10"))
    auto_open = os.getenv("AUTO_OPEN_BROWSER", "true").lower() == "true"
    db_path = os.getenv("TRACKER_DB", "data/careerpilot.db")

    # 1. Collect (resilient, deduplicated)
    from agents.collector.collectors import collect_all

    jobs = collect_all(query=query, sources=sources)

    # 2. Match & rank
    from agents.matcher import rank_jobs

    ranked = rank_jobs(jobs, profile, top_k=top_k)

    if not ranked:
        logger.info("No jobs cleared the match threshold today.")
        return []

    # 3. Set up tracker + cover-letter generation
    from agents.tracker import Tracker
    from agents.coverletter import save_cover_letter

    tracker = Tracker(db_path)
    new_count = 0

    for i, job in enumerate(ranked):
        score = _job_field(job, "score", 0.0)
        key = _job_field(job, "dedup_key", "")

        # Look up prior state (idempotent record_job won't downgrade status).
        already = tracker.get(key) if key else None
        was_new = already is None

        app = tracker.record_job(job, score=score)
        if was_new:
            new_count += 1

        # Generate a tailored cover letter for the top matches only, and only
        # for jobs not already past FOUND (don't regenerate for applied jobs).
        if i < 5 and (already is None or already.status.value == "found"):
            try:
                path = save_cover_letter(job, profile)
                tracker.attach_documents(app.dedup_key, coverletter_path=str(path))
            except Exception as exc:  # noqa: BLE001 — never let one letter abort the run
                logger.warning("Cover letter failed for %s: %s",
                               _job_field(job, "title"), exc)

        # Open top links for you to review and submit.
        if auto_open and i < 5:
            url = _job_field(job, "url")
            if url:
                try:
                    webbrowser.open(url)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Could not open %s: %s", url, exc)

    # 4. Report
    _print_report(ranked, tracker, new_count)
    return ranked


def _print_report(ranked: list, tracker, new_count: int) -> None:
    logger.info("=== Top %d matches (%d new) ===", len(ranked), new_count)
    for job in ranked:
        logger.info(
            "  %.2f  %s @ %s",
            _job_field(job, "score", 0.0),
            _job_field(job, "title"),
            _job_field(job, "company"),
        )
    stats = tracker.stats()
    summary = ", ".join(f"{k}={v}" for k, v in stats.items() if v)
    logger.info("Tracker totals: %s", summary or "none")
    logger.info("Cover letters saved under outputs/coverletters/. "
                "Review, then mark applied with: python view_tracked.py --set <KEY> applied")


if __name__ == "__main__":
    run()
