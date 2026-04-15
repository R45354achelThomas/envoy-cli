"""CLI entry-point for the prefix / strip-prefix commands."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from envoy.parser import EnvParser
from envoy.prefixer import PrefixError, add_prefix, strip_prefix
from envoy.exporter import to_dotenv


def _load_env_file(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return EnvParser(text).parse()


def _write_output(content: str, output: Optional[str]) -> None:
    if output:
        Path(output).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)


def run_prefix(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        env = _load_env_file(args.file)
    except Exception as exc:
        err.write(f"error: could not load '{args.file}': {exc}\n")
        return 1

    try:
        if args.strip:
            result = strip_prefix(
                env,
                args.prefix,
                skip_non_matching=not args.strict,
            )
        else:
            result = add_prefix(
                env,
                args.prefix,
                skip_existing=not args.no_skip,
            )
    except PrefixError as exc:
        err.write(f"error: {exc}\n")
        return 1

    dotenv_text = to_dotenv(result.env)

    if args.output:
        _write_output(dotenv_text, args.output)
        out.write(result.summary() + "\n")
    else:
        out.write(dotenv_text)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy prefix",
        description="Add or strip a prefix from all keys in a .env file.",
    )
    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument("prefix", help="Prefix string to add or strip")
    parser.add_argument(
        "--strip",
        action="store_true",
        default=False,
        help="Strip the prefix instead of adding it (default: add)",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        default=None,
        help="Write result to FILE instead of stdout",
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        default=False,
        help="(add mode) Re-prefix keys that already carry the prefix",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="(strip mode) Raise an error if a key lacks the prefix",
    )
    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_prefix(args))


if __name__ == "__main__":
    main()
