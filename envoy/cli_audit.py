"""CLI sub-command: envoy audit — view the audit log."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.auditor import read_log, AuditEntry


def _format_entry(entry: AuditEntry) -> str:
    detail_str = ""
    if entry.details:
        pairs = ", ".join(f"{k}={v}" for k, v in entry.details.items())
        detail_str = f" [{pairs}]"
    return f"{entry.timestamp}  {entry.user:<12}  {entry.action:<10}  {entry.target}{detail_str}"


def run_audit(
    limit: int = 20,
    action_filter: str | None = None,
    output=None,
) -> int:
    if output is None:
        output = sys.stdout

    entries = read_log(limit=limit)

    if action_filter:
        entries = [e for e in entries if e.action == action_filter]

    if not entries:
        print("No audit entries found.", file=output)
        return 0

    header = f"{'TIMESTAMP':<35} {'USER':<12} {'ACTION':<10} TARGET"
    print(header, file=output)
    print("-" * len(header), file=output)
    for entry in entries:
        print(_format_entry(entry), file=output)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy audit",
        description="Display the envoy-cli audit log.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        metavar="N",
        help="Show last N entries (default: 20).",
    )
    parser.add_argument(
        "--action",
        metavar="ACTION",
        default=None,
        help="Filter by action type (e.g. load, diff, merge).",
    )
    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_audit(limit=args.limit, action_filter=args.action))


if __name__ == "__main__":
    main()
