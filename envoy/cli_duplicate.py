"""CLI entry-point for the `envoy duplicate` sub-command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from envoy.duplicator import DuplicateError, duplicate
from envoy.parser import EnvParser, EnvParseError
from envoy.exporter import to_dotenv


def _load_env_file(path: str) -> dict:
    try:
        text = Path(path).read_text(encoding="utf-8")
        return EnvParser(text).parse()
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _parse_renames(raw: Optional[List[str]]) -> dict:
    """Parse 'OLD=NEW' strings into a dict."""
    mapping = {}
    for item in raw or []:
        if "=" not in item:
            print(f"error: invalid rename spec '{item}' (expected OLD=NEW)", file=sys.stderr)
            sys.exit(1)
        old, new = item.split("=", 1)
        mapping[old.strip()] = new.strip()
    return mapping


def run_duplicate(
    source: str,
    target: str,
    exclude: Optional[List[str]],
    rename: Optional[List[str]],
    in_place: bool,
    stdout,
    stderr,
) -> int:
    env = _load_env_file(source)
    rename_map = _parse_renames(rename)

    try:
        result, output = duplicate(
            env,
            source_path=source,
            target_path=target,
            exclude=exclude,
            rename=rename_map,
        )
    except DuplicateError as exc:
        print(f"error: {exc}", file=stderr)
        return 1

    dotenv_text = to_dotenv(output)

    if in_place or target:
        dest = source if in_place else target
        Path(dest).write_text(dotenv_text, encoding="utf-8")
        print(result.summary(), file=stdout)
    else:
        print(dotenv_text, file=stdout)

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy duplicate",
        description="Duplicate a .env file to a new target with optional key filtering.",
    )
    p.add_argument("source", help="Source .env file")
    p.add_argument("target", nargs="?", default="", help="Destination file (omit to print to stdout)")
    p.add_argument("--exclude", metavar="KEY", action="append", default=[], help="Keys to omit")
    p.add_argument("--rename", metavar="OLD=NEW", action="append", default=[], help="Rename a key")
    p.add_argument("--in-place", action="store_true", help="Overwrite source file")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    sys.exit(
        run_duplicate(
            source=args.source,
            target=args.target,
            exclude=args.exclude,
            rename=args.rename,
            in_place=args.in_place,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    )


if __name__ == "__main__":
    main()
