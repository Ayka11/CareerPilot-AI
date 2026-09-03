"""Helpers for collecting jobs from RSS/Atom and JSON-LD feeds."""

from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.models.job import Job

logger = logging.getLogger(__name__)

USER_AGENT = "CareerPilot-AI/1.0 (+https://github.com/Ayka11/CareerPilot-AI)"
REQUEST_TIMEOUT = 20


def _text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(_text(item) for item in value if _text(item))
    return BeautifulSoup(str(value), "html.parser").get_text(" ", strip=True)


def _date(value) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(str(value)).replace(tzinfo=None)
    except (TypeError, ValueError, IndexError, OverflowError):
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None


def _job(source: str, title: str, company: str, url: str, description="", location="", published="") -> Job | None:
    title = _text(title)
    url = str(url or "").strip()
    if not title or not url:
        return None
    return Job(
        company=_text(company) or "Unknown",
        title=title[:200],
        url=url,
        remote=True,
        location=_text(location) or "Remote",
        description=_text(description),
        source=source,
        created_at=_date(published) or datetime.utcnow(),
    )


def fetch_xml(url: str) -> ET.Element | None:
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        try:
            return ET.fromstring(response.content)
        except ET.ParseError:
            # Some public feeds contain bare ampersands in descriptions.
            repaired = re.sub(rb"&(?!#?\w+;)", b"&amp;", response.content)
            repaired = re.sub(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]", b"", repaired)
            return ET.fromstring(repaired)
    except (requests.RequestException, ET.ParseError) as exc:
        logger.warning("Structured feed %s failed: %s", url, exc)
        return None


def fetch_html(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def parse_feed(url: str, source: str, limit: int = 50) -> list[Job]:
    """Parse RSS 2.0 or Atom entries into normalized jobs."""
    root = fetch_xml(url)
    if root is None:
        return []

    jobs: list[Job] = []
    for entry in root.iter():
        tag = entry.tag.rsplit("}", 1)[-1].lower()
        if tag not in {"item", "entry"}:
            continue
        fields = {
            child.tag.rsplit("}", 1)[-1].lower(): child
            for child in entry
        }
        link_node = fields.get("link")
        link = ""
        if link_node is not None:
            link = link_node.attrib.get("href", "") or _text(link_node.text)
        if not link:
            link = _text(fields.get("guid").text if fields.get("guid") is not None else "")
        job = _job(
            source,
            _text(fields.get("title").text if fields.get("title") is not None else ""),
            _text(fields.get("author").text if fields.get("author") is not None else ""),
            link,
            _text((fields.get("description") or fields.get("summary") or fields.get("content")).text
                  if (fields.get("description") or fields.get("summary") or fields.get("content")) is not None else ""),
            _text(fields.get("location").text if fields.get("location") is not None else "Remote"),
            _text((fields.get("pubdate") or fields.get("published") or fields.get("updated")).text
                  if (fields.get("pubdate") or fields.get("published") or fields.get("updated")) is not None else ""),
        )
        if job:
            jobs.append(job)
        if len(jobs) >= limit:
            break
    logger.info("%s RSS/Atom: collected %d jobs", source, len(jobs))
    return jobs


def parse_jsonld(html: str, source: str, base_url: str, limit: int = 50) -> list[Job]:
    """Extract JobPosting JSON-LD objects from a page without CSS selectors."""
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[Job] = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            payload = json.loads(script.string or script.get_text())
        except (TypeError, json.JSONDecodeError):
            continue
        objects = payload if isinstance(payload, list) else [payload]
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            if obj.get("@type") == "@graph":
                objects.extend(obj.get("@graph", []))
                continue
            types = obj.get("@type", [])
            if "JobPosting" not in (types if isinstance(types, list) else [types]):
                continue
            company = obj.get("hiringOrganization", {})
            if isinstance(company, dict):
                company = company.get("name", "")
            job = _job(
                source,
                obj.get("title", ""),
                company,
                urljoin(base_url, obj.get("url", "")),
                obj.get("description", ""),
                obj.get("jobLocation", "Remote"),
                obj.get("datePosted", ""),
            )
            if job:
                jobs.append(job)
            if len(jobs) >= limit:
                return jobs
    logger.info("%s JSON-LD: collected %d jobs", source, len(jobs))
    return jobs
