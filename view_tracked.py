"""
CLI to view and update tracked applications.

Usage:
    python view_tracked.py                     # list all, grouped by status
    python view_tracked.py --status applied    # filter by status
    python view_tracked.py --stats             # summary counts only
    python view_tracked.py --set KEY applied   # change a status
    python view_tracked.py --history KEY       # full audit trail for one job
"""

from __future__ import annotations

import argparse
import sys

from agents.tracker import Tracker, Status, InvalidTransition


def _print_app(app) -> None:
    score = f"{app.score:.2f}" if app.score else "  - "
    print(f"  [{app.status.value:<9}] {score}  {app.title}  @ {app.company}")
    print(f"             {app.dedup_key}  {app.url}")


def cmd_list(t: Tracker, status: str | None) -> None:
    st = Status(status) if status else None
    apps = t.list_applications(status=st)
    if not apps:
        print("No applications found.")
        return
    print(f"\n{len(apps)} application(s):\n")
    for app in apps:
        _print_app(app)


def cmd_stats(t: Tracker) -> None:
    print("\nApplication summary:")
    for status, count in t.stats().items():
        print(f"  {status:<10} {count}")


def cmd_set(t: Tracker, key: str, status: str) -> None:
    try:
        app = t.set_status(key, Status(status), note="set via view_tracked CLI")
        print(f"Updated: {app.title} -> {app.status.value}")
    except (InvalidTransition, KeyError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_history(t: Tracker, key: str) -> None:
    app = t.get(key)
    if app is None:
        print(f"No application with key {key!r}", file=sys.stderr)
        sys.exit(1)
    print(f"\n{app.title} @ {app.company}")
    for ev in app.history:
        stamp = ev.at.strftime("%Y-%m-%d %H:%M")
        old = ev.old_status or "(new)"
        note = f"  — {ev.note}" if ev.note else ""
        print(f"  {stamp}  {old:>10} -> {ev.new_status:<10}{note}")


def main() -> None:
    p = argparse.ArgumentParser(description="View CareerPilot tracked applications")
    p.add_argument("--db", default="data/careerpilot.db", help="path to the SQLite DB")
    p.add_argument("--status", help="filter list by status")
    p.add_argument("--stats", action="store_true", help="show summary counts")
    p.add_argument("--set", nargs=2, metavar=("KEY", "STATUS"), help="change a status")
    p.add_argument("--history", metavar="KEY", help="show audit trail for one job")
    args = p.parse_args()

    t = Tracker(args.db)
    if args.stats:
        cmd_stats(t)
    elif args.set:
        cmd_set(t, args.set[0], args.set[1])
    elif args.history:
        cmd_history(t, args.history)
    else:
        cmd_list(t, args.status)


if __name__ == "__main__":
    main()
