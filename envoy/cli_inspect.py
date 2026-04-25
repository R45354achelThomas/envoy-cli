"""CLI entry-point for the `envoy inspect` command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from envoy.parser import EnvParser
from envoy.inspector import inspect, InspectError


def _load_env_file(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return EnvParser(text).parse()


def run_inspect(
    env_path: str,
    *,
    show_keys: bool = False,
    output=None,
) -> int:
    out = output or sys.stdout
    try:
        env = _load_env_file(env_path)
    except (OSError, IOError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        result = inspect(env)
    except InspectError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(result.summary(), file=out)

    if show_keys and result.secret_keys:
        print("\nSecret keys:", file=out)
        for k in sorted(result.secret_keys):
            print(f"  {k}", file=out)

    if show_keys and result.empty_keys:
        print("\nEmpty keys:", file=out)
        for k in sorted(result.empty_keys):
            print(f"  {k}", file=out)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy inspect",
        description="Inspect a .env file and display a summary.",
    )
    parser.add_argument("env_file", help="Path to the .env file to inspect")
    parser.add_argument(
        "--show-keys",
        action="store_true",
        default=False,
        help="List secret and empty key names in the output",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_inspect(args.env_file, show_keys=args.show_keys))


if __name__ == "__main__":  # pragma: no cover
    main()
