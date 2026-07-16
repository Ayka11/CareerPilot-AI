"""
Application tracker for CareerPilot AI.

Records every job the pipeline surfaces and tracks its lifecycle through an
explicit status enum. Backed by SQLite via SQLAlchemy (already a dependency).

Design notes
------------
- **Idempotent**: jobs are keyed by their `dedup_key` (title+company hash from
  collectors.py). Re-running the pipeline updates an existing row instead of
  creating duplicates, and never re-surfaces a job you've already acted on.
- **Status lifecycle**: FOUND -> APPLIED -> INTERVIEW -> OFFER, with REJECTED
  and WITHDRAWN reachable from most states. Every transition is written to a
  status-history table so you keep a full audit trail.
- **Self-contained**: importing this module does not touch the DB. The engine
  is created lazily on first use, so tests and other agents can import freely.

Public API:
    tracker = Tracker()                      # or Tracker("data/careerpilot.db")
    tracker.record_job(job, score=0.82)      # insert-or-ignore, returns Application
    tracker.mark_applied(dedup_key)          # convenience transition
    tracker.set_status(dedup_key, Status.INTERVIEW, note="phone screen")
    tracker.list_applications(status=Status.APPLIED)
    tracker.is_seen(dedup_key)               # dedup guard for the collector
    tracker.stats()                          # {status: count}
"""

from __future__ import annotations

import enum
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
    Float,
    DateTime,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    Session,
)

logger = logging.getLogger("careerpilot.tracker")

DEFAULT_DB_PATH = "data/careerpilot.db"


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Status lifecycle
# --------------------------------------------------------------------------- #
class Status(str, enum.Enum):
    FOUND = "found"          # surfaced by matcher, not yet applied
    APPLIED = "applied"      # you submitted an application
    INTERVIEW = "interview"  # interviewing
    OFFER = "offer"          # received an offer
    REJECTED = "rejected"    # closed - not selected
    WITHDRAWN = "withdrawn"  # you pulled out

    def __str__(self) -> str:  # nicer logging / printing
        return self.value


# Allowed forward transitions. REJECTED/WITHDRAWN are reachable from any
# non-terminal state (handled in set_status), so they're omitted here.
_ALLOWED: dict[Status, set[Status]] = {
    Status.FOUND: {Status.APPLIED},
    Status.APPLIED: {Status.INTERVIEW, Status.OFFER},
    Status.INTERVIEW: {Status.OFFER},
    Status.OFFER: set(),
    Status.REJECTED: set(),
    Status.WITHDRAWN: set(),
}
_TERMINAL = {Status.REJECTED, Status.WITHDRAWN}


class InvalidTransition(ValueError):
    """Raised when a status change isn't allowed by the lifecycle."""


# --------------------------------------------------------------------------- #
# ORM models
# --------------------------------------------------------------------------- #
class Base(DeclarativeBase):
    pass


class Application(Base):
    __tablename__ = "applications"

    dedup_key: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    company: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(50), default="")
    location: Mapped[str] = mapped_column(String(200), default="")
    salary: Mapped[str] = mapped_column(String(100), default="")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[Status] = mapped_column(
        SAEnum(Status, values_callable=lambda e: [m.value for m in e]),
        default=Status.FOUND,
        index=True,
    )
    resume_path: Mapped[str] = mapped_column(Text, default="")
    coverletter_path: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    history: Mapped[list["StatusEvent"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="StatusEvent.at",
    )

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"<Application {self.title} @ {self.company} [{self.status}]>"


class StatusEvent(Base):
    __tablename__ = "status_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dedup_key: Mapped[str] = mapped_column(
        ForeignKey("applications.dedup_key", ondelete="CASCADE"), index=True
    )
    old_status: Mapped[str] = mapped_column(String(20), default="")
    new_status: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(Text, default="")
    at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    application: Mapped["Application"] = relationship(back_populates="history")


# --------------------------------------------------------------------------- #
# Field access — accepts Job dataclass or dict
# --------------------------------------------------------------------------- #
def _get(obj, key, default=""):
    val = obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)
    return default if val is None else val


def _job_dedup_key(job) -> str:
    # Prefer the collector's own key; fall back to recomputing it.
    key = _get(job, "dedup_key", "")
    if key:
        return key
    import hashlib
    import re

    def norm(t):
        t = re.sub(r"[^a-z0-9 ]+", " ", str(t).lower())
        return re.sub(r"\s+", " ", t).strip()

    raw = f"{norm(_get(job, 'title'))}::{norm(_get(job, 'company'))}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# Tracker
# --------------------------------------------------------------------------- #
class Tracker:
    """High-level facade over the SQLite database."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        # In-memory DBs (used by tests) don't need a directory.
        if db_path != ":memory:" and not db_path.startswith("sqlite"):
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            url = f"sqlite:///{db_path}"
        elif db_path == ":memory:":
            url = "sqlite:///:memory:"
        else:
            url = db_path
        self.engine = create_engine(url, future=True)
        Base.metadata.create_all(self.engine)

    # -- reads --------------------------------------------------------------
    def is_seen(self, dedup_key: str) -> bool:
        with Session(self.engine) as s:
            return s.get(Application, dedup_key) is not None

    def get(self, dedup_key: str) -> Application | None:
        with Session(self.engine) as s:
            app = s.get(Application, dedup_key)
            if app:
                _ = app.history  # eager-load before session closes
                s.expunge_all()
            return app

    def list_applications(
        self, status: Status | None = None, order_desc: bool = True
    ) -> list[Application]:
        with Session(self.engine) as s:
            stmt = select(Application)
            if status is not None:
                stmt = stmt.where(Application.status == status)
            order = Application.updated_at.desc() if order_desc else Application.updated_at.asc()
            stmt = stmt.order_by(order)
            apps = list(s.scalars(stmt))
            for a in apps:
                _ = a.history
            s.expunge_all()
            return apps

    def stats(self) -> dict[str, int]:
        with Session(self.engine) as s:
            rows = s.execute(
                select(Application.status, func.count()).group_by(Application.status)
            ).all()
        counts = {status.value: 0 for status in Status}
        for status_val, count in rows:
            key = status_val.value if isinstance(status_val, Status) else str(status_val)
            counts[key] = count
        return counts

    # -- writes -------------------------------------------------------------
    def record_job(self, job, score: float | None = None) -> Application:
        """
        Insert a newly-found job, or update mutable fields if it already exists.
        Never downgrades an existing status back to FOUND. Idempotent.
        """
        key = _job_dedup_key(job)
        with Session(self.engine) as s:
            app = s.get(Application, key)
            if app is None:
                app = Application(
                    dedup_key=key,
                    title=str(_get(job, "title")),
                    company=str(_get(job, "company")),
                    url=str(_get(job, "url")),
                    source=str(_get(job, "source")),
                    location=str(_get(job, "location")),
                    salary=str(_get(job, "salary")),
                    score=float(score if score is not None else _get(job, "score", 0.0) or 0.0),
                    status=Status.FOUND,
                )
                s.add(app)
                s.add(StatusEvent(dedup_key=key, old_status="", new_status=Status.FOUND.value,
                                  note="job surfaced by pipeline"))
                logger.info("Recorded new job: %s @ %s", app.title, app.company)
            else:
                # Refresh mutable fields only; keep status/history intact.
                if score is not None:
                    app.score = float(score)
                app.url = str(_get(job, "url")) or app.url
                logger.debug("Job already tracked: %s @ %s", app.title, app.company)
            s.commit()
            _ = app.history
            s.expunge(app)
            return app

    def set_status(
        self, dedup_key: str, new_status: Status, note: str = ""
    ) -> Application:
        """Transition an application, validating the lifecycle and logging it."""
        if not isinstance(new_status, Status):
            new_status = Status(str(new_status))
        with Session(self.engine) as s:
            app = s.get(Application, dedup_key)
            if app is None:
                raise KeyError(f"No application with dedup_key={dedup_key!r}")

            old = app.status
            if old == new_status:
                logger.debug("Status unchanged (%s) for %s", new_status, dedup_key)
                _ = app.history
                s.expunge(app)
                return app

            allowed = _ALLOWED.get(old, set())
            can_close = new_status in _TERMINAL and old not in _TERMINAL
            if new_status not in allowed and not can_close:
                raise InvalidTransition(
                    f"Cannot move {app.title!r} from {old} to {new_status}"
                )

            app.status = new_status
            s.add(StatusEvent(
                dedup_key=dedup_key,
                old_status=old.value,
                new_status=new_status.value,
                note=note,
            ))
            s.commit()
            logger.info("%s: %s -> %s", app.title, old, new_status)
            _ = app.history
            s.expunge(app)
            return app

    # convenience wrappers -------------------------------------------------
    def mark_applied(self, dedup_key: str, note: str = "") -> Application:
        return self.set_status(dedup_key, Status.APPLIED, note or "application submitted")

    def mark_interview(self, dedup_key: str, note: str = "") -> Application:
        return self.set_status(dedup_key, Status.INTERVIEW, note)

    def mark_offer(self, dedup_key: str, note: str = "") -> Application:
        return self.set_status(dedup_key, Status.OFFER, note)

    def mark_rejected(self, dedup_key: str, note: str = "") -> Application:
        return self.set_status(dedup_key, Status.REJECTED, note)

    def mark_withdrawn(self, dedup_key: str, note: str = "") -> Application:
        return self.set_status(dedup_key, Status.WITHDRAWN, note)

    def attach_documents(
        self, dedup_key: str, resume_path: str = "", coverletter_path: str = ""
    ) -> None:
        with Session(self.engine) as s:
            app = s.get(Application, dedup_key)
            if app is None:
                raise KeyError(dedup_key)
            if resume_path:
                app.resume_path = resume_path
            if coverletter_path:
                app.coverletter_path = coverletter_path
            s.commit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    t = Tracker(":memory:")
    job = {"title": "Technical Writer", "company": "Acme", "url": "http://x",
           "source": "remotive", "score": 0.81}
    app = t.record_job(job)
    key = app.dedup_key
    print("seen?", t.is_seen(key))
    t.mark_applied(key)
    t.mark_interview(key, note="30-min phone screen")
    t.mark_offer(key, note="verbal offer")
    final = t.get(key)
    print(f"{final.title} @ {final.company} -> {final.status}")
    print("History:")
    for ev in final.history:
        print(f"  {ev.old_status or '(new)':>10} -> {ev.new_status:<10} {ev.note}")
    print("Stats:", t.stats())
