"""
Cover letter generator for CareerPilot AI.

Two paths, one interface:

1. LLM path — if OPENAI_API_KEY is set and the `openai` package is installed,
   we ask an LLM to tailor a letter to the specific job. The prompt is grounded
   in structured facts from the user's profile, and we instruct the model to
   address 2-3 concrete requirements it extracts from the job description. This
   avoids generic filler and hallucinated experience.

2. Deterministic fallback — always available, no API key, no network. Builds a
   solid, professionally-structured letter from the profile + job using string
   templates. Used automatically when the LLM path is unavailable OR fails, so a
   daily run never silently produces nothing.

Public API:
    generate_cover_letter(job, profile) -> str
    save_cover_letter(job, profile, out_dir="outputs/coverletters") -> Path

`job` may be a Job dataclass (from collectors.py) or a plain dict.
`profile` is the parsed config/profile.yaml as a dict.
"""

from __future__ import annotations

import logging
import os
import re
import textwrap
from datetime import date
from pathlib import Path

logger = logging.getLogger("careerpilot.coverletter")

MODEL = os.getenv("COVERLETTER_MODEL", "gpt-4o-mini")
MAX_JOB_DESC_CHARS = 3500  # keep prompts bounded / cheap


# --------------------------------------------------------------------------- #
# Field access — works for Job dataclass or dict
# --------------------------------------------------------------------------- #
def _field(obj, key: str, default: str = "") -> str:
    if isinstance(obj, dict):
        val = obj.get(key, default)
    else:
        val = getattr(obj, key, default)
    if isinstance(val, list):
        return ", ".join(map(str, val))
    return str(val) if val is not None else default


def _profile_skills(profile: dict) -> list[str]:
    for key in ("skills", "core_skills", "keywords"):
        val = profile.get(key)
        if isinstance(val, list) and val:
            return [str(s) for s in val]
        if isinstance(val, str) and val:
            return [s.strip() for s in val.split(",") if s.strip()]
    return []


def _slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", (text or "").lower())
    return re.sub(r"[\s_-]+", "-", text).strip("-") or "job"


# --------------------------------------------------------------------------- #
# Prompt construction (LLM path)
# --------------------------------------------------------------------------- #
def _build_prompt(job, profile: dict) -> tuple[str, str]:
    name = profile.get("name", "")
    summary = profile.get("summary", "")
    skills = ", ".join(_profile_skills(profile))
    experience = profile.get("experience_highlights") or profile.get("highlights") or ""
    if isinstance(experience, list):
        experience = "; ".join(map(str, experience))

    title = _field(job, "title")
    company = _field(job, "company")
    description = _field(job, "description")[:MAX_JOB_DESC_CHARS]

    system = (
        "You are an expert career writer. You write concise, specific, sincere "
        "cover letters. You NEVER invent employers, titles, degrees, dates, or "
        "achievements that are not present in the candidate facts. If the job "
        "asks for something the candidate lacks, you emphasize adjacent strengths "
        "instead of fabricating. Keep it to ~250-320 words, 3-4 short paragraphs, "
        "no bullet lists, no headers, warm but professional."
    )

    user = textwrap.dedent(
        f"""\
        Write a tailored cover letter for this job.

        === JOB ===
        Title: {title}
        Company: {company}
        Description:
        {description or "(no description provided)"}

        === CANDIDATE FACTS (do not contradict or exceed these) ===
        Name: {name}
        Professional summary: {summary}
        Core skills: {skills}
        Experience highlights: {experience or "(see summary/skills)"}

        === INSTRUCTIONS ===
        1. Open with genuine interest in THIS role at THIS company.
        2. Identify 2-3 concrete requirements or themes from the job description
           and connect each to a real skill or experience from the candidate facts.
        3. Close with a confident, non-pushy call to talk further.
        4. Start directly with the salutation line. Do not include the sender's
           address block, the date, or a subject line — those are added separately.
        5. Sign off with "Sincerely," on its own line followed by the candidate name.
        """
    )
    return system, user


def _generate_llm(job, profile: dict) -> str | None:
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI
    except ImportError:
        logger.info("openai package not installed; using template fallback")
        return None

    try:
        client = OpenAI()
        system, user = _build_prompt(job, profile)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
            max_tokens=600,
        )
        body = (resp.choices[0].message.content or "").strip()
        return body or None
    except Exception as exc:  # noqa: BLE001 — any failure -> fallback
        logger.warning("LLM cover letter failed (%s); using template fallback", exc)
        return None


# --------------------------------------------------------------------------- #
# Deterministic template fallback
# --------------------------------------------------------------------------- #
def _match_skills_to_job(job, profile: dict, limit: int = 3) -> list[str]:
    """Pick profile skills that actually appear in the job text, best-effort."""
    haystack = f"{_field(job, 'title')} {_field(job, 'description')} " \
               f"{_field(job, 'tags')}".lower()
    hits = [s for s in _profile_skills(profile) if s.lower() in haystack]
    if len(hits) < limit:
        for s in _profile_skills(profile):
            if s not in hits:
                hits.append(s)
            if len(hits) >= limit:
                break
    return hits[:limit]


def _generate_template(job, profile: dict) -> str:
    name = profile.get("name", "Your Name")
    summary = profile.get("summary", "").strip()
    title = _field(job, "title") or "the open role"
    company = _field(job, "company") or "your team"
    top_skills = _match_skills_to_job(job, profile)

    if len(top_skills) >= 3:
        skills_sentence = (
            f"My background in {top_skills[0]}, {top_skills[1]}, and "
            f"{top_skills[2]} maps closely to what this role calls for."
        )
    elif top_skills:
        skills_sentence = (
            f"My background in {', '.join(top_skills)} maps closely to what this "
            f"role calls for."
        )
    else:
        skills_sentence = (
            "My professional background maps closely to what this role calls for."
        )

    summary_sentence = (
        f" {summary}" if summary else
        " Over my career I have consistently delivered results across projects and teams."
    )

    body = textwrap.dedent(
        f"""\
        Dear Hiring Team at {company},

        I am writing to express my strong interest in the {title} position. The role
        stood out to me immediately, and I would welcome the chance to contribute to
        {company}'s work.{summary_sentence}

        {skills_sentence} I pride myself on managing multiple priorities, learning
        quickly, and following each project through to a measurable result. I am
        confident I could bring that same focus and reliability to your team.

        I would love to discuss how my experience aligns with your needs. Thank you
        for considering my application — I look forward to the possibility of speaking
        with you.

        Sincerely,
        {name}"""
    )
    return body


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def generate_cover_letter(job, profile: dict) -> str:
    """Return the full cover letter text (header block + body)."""
    body = _generate_llm(job, profile) or _generate_template(job, profile)
    return _prepend_header(body, profile)


def _prepend_header(body: str, profile: dict) -> str:
    """Add a clean sender/date block the LLM was told not to write."""
    lines = [profile.get("name", "")]
    for key in ("email", "phone", "location"):
        if profile.get(key):
            lines.append(str(profile[key]))
    lines = [ln for ln in lines if ln]
    header = "\n".join(lines)
    today = date.today().strftime("%B %d, %Y")
    return f"{header}\n{today}\n\n{body.strip()}\n"


def save_cover_letter(job, profile: dict, out_dir: str = "outputs/coverletters") -> Path:
    """Generate and write the letter to a .txt file. Returns the path."""
    text = generate_cover_letter(job, profile)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fname = f"cover_{_slugify(_field(job, 'company'))}_{_slugify(_field(job, 'title'))}.txt"
    path = out / fname
    path.write_text(text, encoding="utf-8")
    logger.info("Saved cover letter -> %s", path)
    return path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_profile = {
        "name": "Aygun Aliyeva Sundhordvik",
        "email": "aalievaa7@gmail.com",
        "phone": "+994 99 888 0892",
        "location": "Baku, Azerbaijan (Remote)",
        "summary": (
            "Project manager and content writer with 10+ years leading IT and "
            "innovation projects, PRINCE2-certified, with hands-on experience in "
            "SEO content writing, marketing, and technical documentation."
        ),
        "skills": ["project management", "content writing", "SEO", "research",
                   "marketing", "technical documentation"],
        "experience_highlights": [
            "Chief specialist at ANAS leading a Microsoft Partnership Program",
            "SEO content writer at Captain Words (EN-AZ translation)",
            "PRINCE2 Foundation certified international project manager",
        ],
    }
    demo_job = {
        "title": "Remote Technical Content Writer",
        "company": "Doclytics",
        "description": "Seeking a writer to produce SEO-optimized documentation "
                       "and manage a content roadmap. Project management a plus.",
        "tags": ["content writing", "SEO", "documentation"],
    }
    print(generate_cover_letter(demo_job, demo_profile))
