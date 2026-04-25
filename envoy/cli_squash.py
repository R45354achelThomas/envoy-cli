"""CLI entry point: envoy squash — merge multiple .env files into one."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

from envoy.parser import EnvParser
from envoy.squasher import squash, SquashError
from envoy.exporter import to_dotenv, to_json, to_shell


def _load_env_file(path: str) -> Dict[str, str]:
    text = Path(path).read_text(encoding="utf-8")
    return EnvParser(text).parse()


def run_squash(args: argparse.Namespace) -> int:
    try:
        envs = [(_p, _load_env_file(_p)) for _p in args.files]
    except (OSError, Exception) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        result = squash(envs, last_wins=not args.first_wins)
    except SquashError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.verbose:
        for key, old_file, new_file in result.overridden:
            print(f"  override: {key!r}  {old_file} -> {new_file}", file=sys.stderr)
        print(result.summary(), file=sys.stderr)

    fmt = args.format
    if fmt == "json":
        output = to_json(result.env)
    elif fmt == "shell":
        output = to_shell(result.env)
    else:
        output = to_dotenv(result.env)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy squash",
        description="Merge multiple .env files into a single output.",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help=".env files to squash (in order)")
    p.add_argument("-o", "--output", metavar="FILE", help="write result to FILE instead of stdout")
    p.add_argument("--format", choices=["dotenv", "json", "shell"], default="dotenv")
    p.add_argument("--first-wins", action="store_true", help="keep first occurrence on conflict")
    p.add_argument("-v", "--verbose", action="store_true", help="print override details to stderr")
    return p


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_squash(args))


if __name__ == "__main__":
    main()
