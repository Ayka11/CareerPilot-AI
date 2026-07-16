"""
Embedding-based job matcher for CareerPilot AI.

Scores each job against the user's profile using semantic similarity instead of
brittle keyword overlap. This catches relevant jobs that don't share exact
words (important for content/writing roles where phrasing varies widely).

Backends, in order of preference:
1. sentence-transformers (local, free, no API key) — the default.
2. OpenAI embeddings — used only if OPENAI_API_KEY is set AND
   EMBEDDING_BACKEND=openai.
3. Keyword Jaccard fallback — always available, no dependencies. Used
   automatically if no embedding backend can be loaded.

Downstream code calls `rank_jobs(jobs, profile)` and gets jobs back sorted by
score (0..1) with a `.score` attribute attached.
"""

from __future__ import annotations

import logging
import os
import re
from functools import lru_cache

logger = logging.getLogger("careerpilot.matcher")

# Jobs below this relevance score are dropped from results.
DEFAULT_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.35"))
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "auto").lower()
LOCAL_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


# --------------------------------------------------------------------------- #
# Profile → query text
# --------------------------------------------------------------------------- #
def profile_to_text(profile: dict) -> str:
    """Flatten the relevant parts of profile.yaml into one query string."""
    parts: list[str] = []
    if summary := profile.get("summary"):
        parts.append(str(summary))
    for key in ("skills", "core_skills", "target_roles", "keywords"):
        value = profile.get(key)
        if isinstance(value, list):
            parts.append(" ".join(map(str, value)))
        elif value:
            parts.append(str(value))
    return " ".join(parts).strip() or "remote flexible work"


def job_to_text(job) -> str:
    """Build the text we embed for a job. Accepts Job objects or dicts."""
    get = (lambda k: getattr(job, k, "")) if not isinstance(job, dict) else job.get
    tags = get("tags") or []
    tags_str = " ".join(tags) if isinstance(tags, list) else str(tags)
    return " ".join(
        str(x) for x in [get("title"), get("company"), tags_str, get("description")] if x
    ).strip()


# --------------------------------------------------------------------------- #
# Backend selection (cached so the model loads once)
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def _load_local_model():
    from sentence_transformers import SentenceTransformer  # lazy import

    logger.info("Loading local embedding model: %s", LOCAL_MODEL)
    return SentenceTransformer(LOCAL_MODEL)


def _embed_local(texts: list[str]):
    model = _load_local_model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)


def _embed_openai(texts: list[str]):
    from openai import OpenAI  # lazy import

    client = OpenAI()  # reads OPENAI_API_KEY from env
    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    resp = client.embeddings.create(model=model, input=texts)
    import numpy as np

    vecs = np.array([d.embedding for d in resp.data], dtype="float32")
    # normalize so dot product == cosine similarity
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / (norms + 1e-9)


def _choose_backend():
    """Return an embed function, or None to signal keyword fallback."""
    if EMBEDDING_BACKEND == "openai" or (
        EMBEDDING_BACKEND == "auto" and os.getenv("OPENAI_API_KEY")
        and EMBEDDING_BACKEND != "local"
    ):
        try:
            import openai  # noqa: F401
            if os.getenv("OPENAI_API_KEY"):
                logger.info("Matcher backend: OpenAI embeddings")
                return _embed_openai
        except ImportError:
            pass

    try:
        import sentence_transformers  # noqa: F401
        logger.info("Matcher backend: local sentence-transformers")
        return _embed_local
    except ImportError:
        logger.warning(
            "No embedding backend available — falling back to keyword matching. "
            "Install 'sentence-transformers' for much better results."
        )
        return None


# --------------------------------------------------------------------------- #
# Keyword fallback
# --------------------------------------------------------------------------- #
def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def score_jobs(jobs: list, profile: dict) -> list[tuple]:
    """Return list of (job, score) using the best available backend."""
    if not jobs:
        return []

    profile_text = profile_to_text(profile)
    job_texts = [job_to_text(j) for j in jobs]
    embed = _choose_backend()

    if embed is None:
        return [(job, _jaccard(profile_text, jt)) for job, jt in zip(jobs, job_texts)]

    try:
        import numpy as np

        prof_vec = embed([profile_text])[0]
        job_vecs = embed(job_texts)
        scores = np.asarray(job_vecs) @ np.asarray(prof_vec)
        # cosine on normalized vectors is in [-1,1]; clamp to [0,1] for sanity
        scores = [(float(s) + 1.0) / 2.0 for s in scores]
        return list(zip(jobs, scores))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Embedding scoring failed (%s) — using keyword fallback", exc)
        return [(job, _jaccard(profile_text, jt)) for job, jt in zip(jobs, job_texts)]


def rank_jobs(
    jobs: list,
    profile: dict,
    threshold: float | None = None,
    top_k: int | None = None,
) -> list:
    """
    Score, filter by threshold, sort descending, optionally truncate to top_k.
    Attaches a `.score` attribute (or ['score'] key for dicts) to each job.
    """
    if threshold is None:
        # Read at call time so env overrides (e.g. in tests) take effect even
        # though this module was imported earlier.
        threshold = float(os.getenv("MATCH_THRESHOLD", str(DEFAULT_THRESHOLD)))
    scored = score_jobs(jobs, profile)

    ranked = []
    for job, score in scored:
        if score < threshold:
            continue
        if isinstance(job, dict):
            job["score"] = round(score, 4)
        else:
            setattr(job, "score", round(score, 4))
        ranked.append(job)

    ranked.sort(
        key=lambda j: j["score"] if isinstance(j, dict) else j.score, reverse=True
    )
    if top_k:
        ranked = ranked[:top_k]
    logger.info("Ranked %d/%d jobs above threshold %.2f", len(ranked), len(jobs), threshold)
    return ranked


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_profile = {
        "summary": "Technical writer and content strategist with research and PM experience.",
        "skills": ["technical writing", "documentation", "content creation", "research"],
    }
    demo_jobs = [
        {"title": "Senior Technical Writer", "company": "Acme", "description": "Write docs and API guides.", "tags": ["writing"]},
        {"title": "Backend Kubernetes Engineer", "company": "Infra Co", "description": "Go, distributed systems.", "tags": ["golang"]},
        {"title": "Content Strategist (Remote)", "company": "Beta", "description": "Own content roadmap and research.", "tags": ["content"]},
    ]
    for j in rank_jobs(demo_jobs, demo_profile, threshold=0.0):
        print(f"{j['score']:.3f}  {j['title']}")
