"""CLI entry-point for the strip command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from envoy.parser import EnvParser
from envoy.stripper import strip
from envoy.exporter import to_dotenv


def _load_env_file(path: str) -> dict:
    return EnvParser(Path(path).read_text()).parse()


def _write_output(content: str, output: Optional[str]) -> None:
    if output:
        Path(output).write_text(content)
    else:
        print(content, end="")


def run_strip(
    input_path: str,
    keys: Optional[List[str]] = None,
    patterns: Optional[List[str]] = None,
    prefix: Optional[str] = None,
    output: Optional[str] = None,
    quiet: bool = False,
) -> int:
    env = _load_env_file(input_path)
    result = strip(env, keys=keys, patterns=patterns, prefix=prefix)

    if not quiet:
        print(result.summary(), file=sys.stderr)

    _write_output(to_dotenv(result.env), output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy strip",
        description="Remove keys from a .env file by name, prefix, or pattern.",
    )
    p.add_argument("input", help="Path to the source .env file.")
    p.add_argument(
        "-k", "--key",
        dest="keys",
        metavar="KEY",
        action="append",
        help="Exact key name to strip (repeatable).",
    )
    p.add_argument(
        "-p", "--pattern",
        dest="patterns",
        metavar="REGEX",
        action="append",
        help="Regex pattern; matching keys are stripped (repeatable).",
    )
    p.add_argument(
        "--prefix",
        metavar="PREFIX",
        help="Strip all keys that start with PREFIX.",
    )
    p.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Write result to FILE instead of stdout.",
    )
    p.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress summary output.",
    )
    return p


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(
        run_strip(
            input_path=args.input,
            keys=args.keys,
            patterns=args.patterns,
            prefix=args.prefix,
            output=args.output,
            quiet=args.quiet,
        )
    )


if __name__ == "__main__":
    main()
