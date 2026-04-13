"""CLI sub-commands for snapshot management: save, load, list, delete."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.parser import EnvParser
from envoy.snapshotter import (
    SnapshotError,
    delete_snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
    DEFAULT_SNAPSHOT_DIR,
)


def _load_env_file(path: str) -> dict:
    parser = EnvParser()
    with open(path, encoding="utf-8") as fh:
        return dict(parser.parse(fh.read()))


def run_snapshot(args: argparse.Namespace) -> int:
    snap_dir = Path(args.snapshot_dir)

    if args.action == "save":
        try:
            values = _load_env_file(args.env_file)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        tags = args.tags.split(",") if args.tags else []
        snap = save_snapshot(
            name=args.name,
            values=values,
            env_file=args.env_file,
            tags=tags,
            snapshot_dir=snap_dir,
        )
        print(f"Saved snapshot '{snap.name}' ({len(snap.values)} keys) at {snap.created_at}")
        return 0

    if args.action == "load":
        try:
            snap = load_snapshot(args.name, snapshot_dir=snap_dir)
        except SnapshotError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        for key, value in snap.values.items():
            print(f"{key}={value}")
        return 0

    if args.action == "list":
        snaps = list_snapshots(snapshot_dir=snap_dir)
        if not snaps:
            print("No snapshots found.")
            return 0
        for snap in snaps:
            tags_str = f"  [{', '.join(snap.tags)}]" if snap.tags else ""
            print(f"{snap.name:<30} {snap.created_at}  {snap.env_file}{tags_str}")
        return 0

    if args.action == "delete":
        try:
            delete_snapshot(args.name, snapshot_dir=snap_dir)
            print(f"Deleted snapshot '{args.name}'.")
        except SnapshotError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        return 0

    print(f"Unknown action: {args.action}", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Manage .env snapshots")
    p.add_argument("--snapshot-dir", default=str(DEFAULT_SNAPSHOT_DIR),
                   help="Directory to store snapshots (default: .env-snapshots)")
    sub = p.add_subparsers(dest="action", required=True)

    save_p = sub.add_parser("save", help="Save a snapshot")
    save_p.add_argument("name", help="Snapshot name")
    save_p.add_argument("env_file", help="Path to .env file")
    save_p.add_argument("--tags", default="", help="Comma-separated tags")

    load_p = sub.add_parser("load", help="Print a snapshot's key=value pairs")
    load_p.add_argument("name", help="Snapshot name")

    sub.add_parser("list", help="List all snapshots")

    del_p = sub.add_parser("delete", help="Delete a snapshot")
    del_p.add_argument("name", help="Snapshot name")

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_snapshot(args))


if __name__ == "__main__":
    main()
