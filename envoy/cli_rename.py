"""CLI entry-point for the *rename* sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from envoy.parser import EnvParser
from envoy.renamer import RenameError, rename
from envoy.exporter import to_dotenv


def _load_env_file(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return EnvParser(text).parse()


def _parse_renames(pairs: List[str]) -> dict:
    """Convert ``OLD=NEW`` strings into a rename mapping."""
    mapping: dict = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid rename spec {pair!r}: expected OLD=NEW format")
        old, _, new = pair.partition("=")
        mapping[old.strip()] = new.strip()
    return mapping


def run_rename(
    env_path: str,
    rename_pairs: List[str],
    *,
    allow_overwrite: bool = False,
    output: str | None = None,
    in_place: bool = False,
    quiet: bool = False,
) -> int:
    try:
        env = _load_env_file(env_path)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not load '{env_path}': {exc}", file=sys.stderr)
        return 1

    try:
        renames = _parse_renames(rename_pairs)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        result = rename(env, renames, allow_overwrite=allow_overwrite)
    except RenameError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not quiet:
        print(result.summary())
        for old, new in result.renamed:
            print(f"  renamed: {old} -> {new}")
        for key, reason in result.skipped:
            print(f"  skipped: {key} ({reason})")

    dotenv_output = to_dotenv(result.env)
    dest = env_path if in_place else output
    if dest:
        Path(dest).write_text(dotenv_output, encoding="utf-8")
    else:
        print(dotenv_output)

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy rename",
        description="Rename one or more keys in a .env file.",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument(
        "renames",
        nargs="+",
        metavar="OLD=NEW",
        help="Key rename specs in OLD=NEW format",
    )
    p.add_argument("--allow-overwrite", action="store_true", help="Allow clobbering existing keys")
    p.add_argument("--output", "-o", metavar="FILE", help="Write result to FILE instead of stdout")
    p.add_argument("--in-place", "-i", action="store_true", help="Overwrite the source file")
    p.add_argument("--quiet", "-q", action="store_true", help="Suppress informational output")
    return p


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(
        run_rename(
            args.env_file,
            args.renames,
            allow_overwrite=args.allow_overwrite,
            output=args.output,
            in_place=args.in_place,
            quiet=args.quiet,
        )
    )


if __name__ == "__main__":
    main()
