"""CLI entry-point for patching .env files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

from envoy.patcher import PatchError, patch_file


def _parse_assignments(items: list[str]) -> Dict[str, str]:
    """Convert ['KEY=val', ...] into a dict, raising on bad format."""
    result: Dict[str, str] = {}
    for item in items:
        if '=' not in item:
            raise argparse.ArgumentTypeError(
                f"Invalid assignment (expected KEY=VALUE): {item!r}"
            )
        key, _, value = item.partition('=')
        key = key.strip()
        if not key:
            raise argparse.ArgumentTypeError(f"Empty key in assignment: {item!r}")
        result[key] = value
    return result


def run_patch(
    env_path: Path,
    assignments: Dict[str, str],
    *,
    add_missing: bool = True,
    preserve_quotes: bool = False,
    quiet: bool = False,
    out=None,
    err=None,
) -> int:
    """Patch *env_path* with *assignments*. Returns exit code."""
    out = out or sys.stdout
    err = err or sys.stderr

    try:
        result = patch_file(
            env_path,
            assignments,
            add_missing=add_missing,
            preserve_quotes=preserve_quotes,
        )
    except PatchError as exc:
        print(f"error: {exc}", file=err)
        return 1

    if not quiet:
        print(result.summary(), file=out)
        for key, val in result.applied.items():
            print(f"  updated  {key}={val}", file=out)
        for key, val in result.added.items():
            print(f"  added    {key}={val}", file=out)

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy patch",
        description="Apply KEY=VALUE patches to a .env file in-place.",
    )
    p.add_argument("env_file", type=Path, help="Target .env file to patch.")
    p.add_argument(
        "assignments",
        nargs="+",
        metavar="KEY=VALUE",
        help="One or more KEY=VALUE assignments to apply.",
    )
    p.add_argument(
        "--no-add",
        dest="add_missing",
        action="store_false",
        default=True,
        help="Do not append keys that are absent from the file.",
    )
    p.add_argument(
        "--preserve-quotes",
        action="store_true",
        default=False,
        help="Keep the original quoting style when updating a value.",
    )
    p.add_argument(
        "-q", "--quiet",
        action="store_true",
        default=False,
        help="Suppress output.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        patches = _parse_assignments(args.assignments)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
        return
    sys.exit(
        run_patch(
            args.env_file,
            patches,
            add_missing=args.add_missing,
            preserve_quotes=args.preserve_quotes,
            quiet=args.quiet,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
