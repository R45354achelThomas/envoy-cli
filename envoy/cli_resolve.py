"""CLI entry-point for the `envoy resolve` command."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy.resolver import resolve, ResolveError


def run_resolve(
    file_paths: List[str],
    *,
    first_wins: bool = False,
    show_sources: bool = False,
    key_filter: Optional[str] = None,
    output=None,
) -> int:
    """Resolve variables and print the result.  Returns an exit code."""
    out = output or sys.stdout
    try:
        env = resolve(file_paths, last_wins=not first_wins)
    except ResolveError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    items = sorted(env.values.items())
    if key_filter:
        items = [(k, v) for k, v in items if key_filter.lower() in k.lower()]

    if not items:
        print("(no variables matched)", file=out)
        return 0

    for key, value in items:
        if show_sources:
            source = env.source_of(key) or "?"
            overridden = " [overridden]" if env.was_overridden(key) else ""
            print(f"{key}={value}  # {source}{overridden}", file=out)
        else:
            print(f"{key}={value}", file=out)

    print("", file=out)
    print(env.summary(), file=out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy resolve",
        description="Resolve .env variables from multiple files with precedence rules.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more .env files (later files override earlier ones by default).",
    )
    parser.add_argument(
        "--first-wins",
        action="store_true",
        default=False,
        help="Use first-definition-wins strategy instead of last.",
    )
    parser.add_argument(
        "--show-sources",
        action="store_true",
        default=False,
        help="Annotate each variable with its source file.",
    )
    parser.add_argument(
        "--filter",
        dest="key_filter",
        metavar="PATTERN",
        default=None,
        help="Only show keys containing PATTERN (case-insensitive).",
    )
    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(
        run_resolve(
            args.files,
            first_wins=args.first_wins,
            show_sources=args.show_sources,
            key_filter=args.key_filter,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
