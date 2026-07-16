"""
Offline tests for CareerPilot. No network calls — collectors are exercised via
their pure helpers and the matcher via its keyword fallback, so `pytest` runs
green in CI without API keys or internet.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.collector.collectors import Job, deduplicate, _normalize, _strip_html
from agents.matcher import rank_jobs, profile_to_text, job_to_text


# --------------------------- collector helpers ---------------------------- #
def test_normalize_strips_punct_and_case():
    assert _normalize("Technical  Writer!!") == "technical writer"
    assert _normalize("ACME, Inc.") == "acme inc"


def test_strip_html():
    assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"


def test_dedup_collapses_cross_source_duplicates():
    jobs = [
        Job(source="remoteok", title="Technical Writer", company="Acme", url="a"),
        Job(source="remotive", title="Technical  Writer!", company="ACME", url="b"),
        Job(source="remotive", title="Content Strategist", company="Beta", url="c"),
    ]
    out = deduplicate(jobs)
    assert len(out) == 2
    assert {j.company for j in out} == {"Acme", "Beta"}


def test_dedup_drops_incomplete_records():
    jobs = [Job(source="x", title="", company="Acme", url="a")]
    assert deduplicate(jobs) == []


def test_dedup_key_is_stable():
    a = Job(source="s", title="Data Analyst", company="Foo", url="1")
    b = Job(source="t", title="data analyst", company="FOO", url="2")
    assert a.dedup_key == b.dedup_key


# ------------------------------- matcher ---------------------------------- #
def test_profile_to_text_includes_skills():
    text = profile_to_text({"summary": "Writer.", "skills": ["docs", "research"]})
    assert "docs" in text and "research" in text and "Writer" in text


def test_job_to_text_handles_dict_and_object():
    d = {"title": "Writer", "company": "Acme", "tags": ["a"], "description": "x"}
    assert "Writer" in job_to_text(d)
    j = Job(source="s", title="Writer", company="Acme", url="u", tags=["a"])
    assert "Writer" in job_to_text(j)


def test_ranking_orders_relevant_jobs_higher():
    profile = {"summary": "Technical writer and content strategist",
               "skills": ["technical writing", "documentation", "research"]}
    jobs = [
        {"title": "Kubernetes Engineer", "company": "Infra",
         "description": "Go distributed systems", "tags": ["golang"]},
        {"title": "Senior Technical Writer", "company": "Acme",
         "description": "Write API documentation and guides", "tags": ["writing"]},
    ]
    ranked = rank_jobs(jobs, profile, threshold=0.0)
    assert ranked[0]["title"] == "Senior Technical Writer"


def test_threshold_filters_low_scores():
    profile = {"skills": ["writing"]}
    jobs = [{"title": "Nuclear Physicist", "company": "X",
             "description": "quantum reactors", "tags": []}]
    assert rank_jobs(jobs, profile, threshold=0.9) == []


def test_top_k_truncates():
    profile = {"skills": ["writing"]}
    jobs = [{"title": f"Writer {i}", "company": "C", "description": "writing",
             "tags": []} for i in range(20)]
    assert len(rank_jobs(jobs, profile, threshold=0.0, top_k=5)) == 5


# --------------------------- cover letter --------------------------------- #
from agents.coverletter import (
    generate_cover_letter,
    _generate_template,
    _match_skills_to_job,
    _slugify,
)

_CL_PROFILE = {
    "name": "Aygun Aliyeva",
    "email": "a@example.com",
    "location": "Remote",
    "summary": "Project manager and content writer.",
    "skills": ["project management", "content writing", "SEO", "research"],
}
_CL_JOB = {
    "title": "Technical Content Writer",
    "company": "Doclytics",
    "description": "SEO documentation and content roadmap. Project management a plus.",
    "tags": ["content writing", "SEO"],
}


def test_template_letter_contains_key_fields():
    letter = _generate_template(_CL_JOB, _CL_PROFILE)
    assert "Doclytics" in letter
    assert "Technical Content Writer" in letter
    assert "Aygun Aliyeva" in letter
    assert letter.strip().endswith("Aygun Aliyeva")


def test_match_skills_prioritizes_job_mentioned_skills():
    hits = _match_skills_to_job(_CL_JOB, _CL_PROFILE, limit=3)
    # SEO and content writing appear in the job text -> should be selected
    assert "SEO" in hits
    assert "content writing" in hits


def test_generate_cover_letter_adds_header_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    letter = generate_cover_letter(_CL_JOB, _CL_PROFILE)
    assert "a@example.com" in letter        # header block present
    assert "Doclytics" in letter            # body present
    assert "Sincerely," in letter


def test_slugify():
    assert _slugify("Doclytics, Inc.") == "doclytics-inc"
    assert _slugify("") == "job"


# ------------------------------ tracker ----------------------------------- #
import pytest
from agents.tracker import Tracker, Status, InvalidTransition

_TRACK_JOB = {"title": "Technical Writer", "company": "Acme", "url": "http://x",
              "source": "remotive", "score": 0.8}


def _fresh_tracker():
    return Tracker(":memory:")


def test_record_job_is_idempotent():
    t = _fresh_tracker()
    a1 = t.record_job(_TRACK_JOB)
    a2 = t.record_job(_TRACK_JOB)  # same job again
    assert a1.dedup_key == a2.dedup_key
    assert len(t.list_applications()) == 1


def test_is_seen_guards_duplicates():
    t = _fresh_tracker()
    app = t.record_job(_TRACK_JOB)
    assert t.is_seen(app.dedup_key) is True
    assert t.is_seen("nonexistent") is False


def test_valid_lifecycle_transitions():
    t = _fresh_tracker()
    key = t.record_job(_TRACK_JOB).dedup_key
    assert t.mark_applied(key).status == Status.APPLIED
    assert t.mark_interview(key).status == Status.INTERVIEW
    assert t.mark_offer(key).status == Status.OFFER


def test_invalid_transition_raises():
    t = _fresh_tracker()
    key = t.record_job(_TRACK_JOB).dedup_key
    # FOUND -> INTERVIEW skips APPLIED and is not allowed
    with pytest.raises(InvalidTransition):
        t.set_status(key, Status.INTERVIEW)


def test_rejected_reachable_from_applied():
    t = _fresh_tracker()
    key = t.record_job(_TRACK_JOB).dedup_key
    t.mark_applied(key)
    assert t.mark_rejected(key, note="not selected").status == Status.REJECTED


def test_status_history_is_recorded():
    t = _fresh_tracker()
    key = t.record_job(_TRACK_JOB).dedup_key
    t.mark_applied(key)
    app = t.get(key)
    transitions = [(e.old_status, e.new_status) for e in app.history]
    assert ("", "found") in transitions
    assert ("found", "applied") in transitions


def test_record_does_not_downgrade_status():
    t = _fresh_tracker()
    key = t.record_job(_TRACK_JOB).dedup_key
    t.mark_applied(key)
    t.record_job(_TRACK_JOB)  # re-surface should NOT reset to found
    assert t.get(key).status == Status.APPLIED


def test_list_filtered_by_status():
    t = _fresh_tracker()
    k1 = t.record_job(_TRACK_JOB).dedup_key
    t.record_job({"title": "Content Strategist", "company": "Beta", "url": "y"})
    t.mark_applied(k1)
    applied = t.list_applications(status=Status.APPLIED)
    assert len(applied) == 1 and applied[0].company == "Acme"


def test_stats_counts_by_status():
    t = _fresh_tracker()
    k = t.record_job(_TRACK_JOB).dedup_key
    t.mark_applied(k)
    stats = t.stats()
    assert stats["applied"] == 1 and stats["found"] == 0


def test_attach_documents():
    t = _fresh_tracker()
    key = t.record_job(_TRACK_JOB).dedup_key
    t.attach_documents(key, coverletter_path="outputs/coverletters/x.txt")
    assert t.get(key).coverletter_path.endswith("x.txt")


# ------------------------- orchestrator wiring ---------------------------- #
def test_orchestrator_pipeline_wiring(monkeypatch, tmp_path):
    """End-to-end: collection is mocked; verify records + cover letters + tracker."""
    import agents.core.orchestrator as orch
    import agents.collector.collectors as collectors
    from agents.collector.collectors import Job

    fake_jobs = [
        Job(source="remotive", title="Technical Writer", company="Acme",
            url="http://acme/job", description="Write SEO docs", tags=["writing", "SEO"]),
        Job(source="remoteok", title="Content Strategist", company="Beta",
            url="http://beta/job", description="Own content roadmap", tags=["content"]),
    ]
    fake_profile = {
        "name": "Test User", "email": "t@example.com",
        "summary": "Technical writer and content strategist.",
        "skills": ["technical writing", "SEO", "content", "documentation"],
        "target_roles": ["Technical Writer"],
        "sources": ["remotive", "remoteok"],
    }

    monkeypatch.setattr(orch, "_load_env", lambda: None)
    monkeypatch.setattr(orch, "_load_profile", lambda: fake_profile)
    # Orchestrator imports collect_all from this module at call time.
    monkeypatch.setattr(collectors, "collect_all",
                        lambda query="", sources=None: fake_jobs)
    monkeypatch.setenv("AUTO_OPEN_BROWSER", "false")
    monkeypatch.setenv("TRACKER_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("MATCH_THRESHOLD", "0.0")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)

    ranked = orch.run()
    assert len(ranked) == 2

    from agents.tracker import Tracker, Status
    t = Tracker(str(tmp_path / "test.db"))
    apps = t.list_applications()
    assert len(apps) == 2
    assert all(a.status == Status.FOUND for a in apps)
    assert all(a.coverletter_path for a in apps)

    letters = list((tmp_path / "outputs" / "coverletters").glob("*.txt"))
    assert len(letters) == 2


def test_orchestrator_is_idempotent_across_runs(monkeypatch, tmp_path):
    """Running twice must not create duplicate applications."""
    import agents.core.orchestrator as orch
    import agents.collector.collectors as collectors
    from agents.collector.collectors import Job

    fake_jobs = [Job(source="remotive", title="Technical Writer", company="Acme",
                     url="http://x", description="docs", tags=["writing"])]
    fake_profile = {"name": "T", "skills": ["technical writing"],
                    "target_roles": ["Writer"], "sources": ["remotive"]}

    monkeypatch.setattr(orch, "_load_env", lambda: None)
    monkeypatch.setattr(orch, "_load_profile", lambda: fake_profile)
    monkeypatch.setattr(collectors, "collect_all",
                        lambda query="", sources=None: fake_jobs)
    monkeypatch.setenv("AUTO_OPEN_BROWSER", "false")
    monkeypatch.setenv("TRACKER_DB", str(tmp_path / "t.db"))
    monkeypatch.setenv("MATCH_THRESHOLD", "0.0")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)

    orch.run()
    orch.run()

    from agents.tracker import Tracker
    t = Tracker(str(tmp_path / "t.db"))
    assert len(t.list_applications()) == 1
