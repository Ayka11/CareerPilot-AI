"""
Resilient multi-source job collector for CareerPilot AI.

Design principles
-----------------
1. API-first: use official JSON APIs where they exist (Remotive, RemoteOK).
2. Isolation: each source runs in its own try/except so one broken source
   never kills the whole run.
3. Normalization: every source returns a list of `Job` objects with the
   same shape, so downstream agents (matcher, dedup) don't care about origin.
4. No LinkedIn scraping: LinkedIn's ToS prohibits scraping and will get your
   IP flagged. We rely on compliant sources and leave a documented stub.

Dependencies: requests (see requirements.txt).
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Iterable

import requests

logger = logging.getLogger("careerpilot.collector")

# Be a good citizen: identify the bot and give a contact.
USER_AGENT = "CareerPilot-AI/1.0 (+https://github.com/Ayka11/CareerPilot-AI)"
REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # seconds, doubled each retry


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Job:
    """Normalized job posting. Every collector returns these."""

    source: str
    title: str
    company: str
    url: str
    description: str = ""
    location: str = ""
    tags: list[str] = field(default_factory=list)
    salary: str = ""
    posted_at: str = ""

    @property
    def dedup_key(self) -> str:
        """Stable hash of (normalized title + company) for deduplication."""
        norm = f"{_normalize(self.title)}::{_normalize(self.company)}"
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["dedup_key"] = self.dedup_key
        return d


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation and collapse whitespace for stable keys."""
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _strip_html(raw: str) -> str:
    """Very light HTML tag stripper — enough for matching, not for display."""
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _get(url: str, **kwargs) -> requests.Response | None:
    """GET with retries and exponential backoff. Returns None on total failure."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    headers.update(kwargs.pop("headers", {}))
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            wait = RETRY_BACKOFF * (2 ** (attempt - 1))
            logger.warning("GET %s failed (attempt %d/%d): %s", url, attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(wait)
    logger.error("GET %s failed after %d attempts", url, MAX_RETRIES)
    return None


# --------------------------------------------------------------------------- #
# Individual collectors — each returns list[Job], never raises
# --------------------------------------------------------------------------- #
def collect_remotive(query: str = "") -> list[Job]:
    """
    Remotive public API: https://remotive.com/api/remote-jobs
    Supports ?search= and ?category=. Returns clean JSON — no scraping needed.
    """
    url = "https://remotive.com/api/remote-jobs"
    params = {"search": query} if query else {}
    resp = _get(url, params=params)
    if resp is None:
        return []
    try:
        data = resp.json()
    except ValueError:
        logger.error("Remotive returned non-JSON")
        return []

    jobs: list[Job] = []
    for item in data.get("jobs", []):
        jobs.append(
            Job(
                source="remotive",
                title=item.get("title", "").strip(),
                company=item.get("company_name", "").strip(),
                url=item.get("url", ""),
                description=_strip_html(item.get("description", "")),
                location=item.get("candidate_required_location", "Remote"),
                tags=item.get("tags", []) or [],
                salary=item.get("salary", "") or "",
                posted_at=item.get("publication_date", ""),
            )
        )
    logger.info("Remotive: collected %d jobs", len(jobs))
    return jobs


def collect_remoteok(query: str = "") -> list[Job]:
    """
    RemoteOK API: https://remoteok.com/api
    First element is legal/metadata — skip it. Filtering by query is client-side.
    """
    url = "https://remoteok.com/api"
    resp = _get(url)
    if resp is None:
        return []
    try:
        data = resp.json()
    except ValueError:
        logger.error("RemoteOK returned non-JSON")
        return []

    q = _normalize(query)
    jobs: list[Job] = []
    for item in data:
        # Skip the legal notice object (has no 'position').
        if not isinstance(item, dict) or "position" not in item:
            continue
        title = item.get("position", "").strip()
        tags = item.get("tags", []) or []
        haystack = _normalize(f"{title} {' '.join(tags)} {item.get('description','')}")
        if q and q not in haystack:
            continue
        jobs.append(
            Job(
                source="remoteok",
                title=title,
                company=item.get("company", "").strip(),
                url=item.get("url", "") or item.get("apply_url", ""),
                description=_strip_html(item.get("description", "")),
                location=item.get("location", "Remote") or "Remote",
                tags=tags,
                salary=_format_salary(item.get("salary_min"), item.get("salary_max")),
                posted_at=item.get("date", ""),
            )
        )
    logger.info("RemoteOK: collected %d jobs (query=%r)", len(jobs), query)
    return jobs


def collect_linkedin(query: str = "") -> list[Job]:
    """
    LinkedIn scraping violates their ToS and will get your IP flagged/blocked.
    Intentionally returns [] and logs guidance. To include LinkedIn jobs,
    use their official partner feed or apply manually via auto-opened links
    from the compliant sources above.
    """
    logger.info(
        "LinkedIn collector disabled by design (ToS). "
        "Use official partner feeds if you have access."
    )
    return []


def _format_salary(lo, hi) -> str:
    if lo and hi:
        return f"${lo:,}–${hi:,}"
    if lo:
        return f"${lo:,}+"
    return ""


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
# Registry maps a name -> callable. Add new sources here.
COLLECTORS = {
    "remotive": collect_remotive,
    "remoteok": collect_remoteok,
    "linkedin": collect_linkedin,
}


def collect_all(query: str = "", sources: Iterable[str] | None = None) -> list[Job]:
    """
    Run every requested collector in isolation and merge + deduplicate results.

    Returns a flat, deduplicated list of Job objects. A failure in one source
    is logged and skipped; it never aborts the run.
    """
    sources = list(sources) if sources else list(COLLECTORS.keys())
    all_jobs: list[Job] = []
    succeeded, failed = [], []

    for name in sources:
        collector = COLLECTORS.get(name)
        if collector is None:
            logger.warning("Unknown source %r — skipping", name)
            continue
        try:
            jobs = collector(query)
            all_jobs.extend(jobs)
            succeeded.append(name)
        except Exception as exc:  # noqa: BLE001 — isolation is the whole point
            logger.exception("Source %r crashed: %s", name, exc)
            failed.append(name)

    deduped = deduplicate(all_jobs)
    logger.info(
        "Collection complete: %d raw → %d unique | ok=%s failed=%s",
        len(all_jobs), len(deduped), succeeded, failed or "none",
    )
    return deduped


def deduplicate(jobs: list[Job]) -> list[Job]:
    """Drop duplicate postings that appear across sources (title+company)."""
    seen: set[str] = set()
    unique: list[Job] = []
    for job in jobs:
        if not job.title or not job.company:
            continue
        if job.dedup_key in seen:
            continue
        seen.add(job.dedup_key)
        unique.append(job)
    return unique


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    results = collect_all(query="technical writer")
    for j in results[:10]:
        print(f"[{j.source}] {j.title} @ {j.company} — {j.url}")
    print(f"\nTotal unique jobs: {len(results)}")
