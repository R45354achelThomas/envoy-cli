"""CLI interface for the trimmer module."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from envoy.parser import EnvParser
from envoy.trimmer import trim
from envoy.exporter import to_dotenv


def _load_env_file(path: str) -> dict:
    parser = EnvParser()
    with open(path, "r", encoding="utf-8") as fh:
        return parser.parse(fh.read())


def _write_output(content: str, output: Optional[str]) -> None:
    if output:
        Path(output).write_text(content, encoding="utf-8")
    else:
        print(content, end="")


def run_trim(
    input_path: str,
    output_path: Optional[str] = None,
    *,
    in_place: bool = False,
    no_strip_keys: bool = False,
    no_strip_values: bool = False,
    normalize_empty: bool = False,
    quiet: bool = False,
) -> int:
    """Run the trim command. Returns exit code."""
    env = _load_env_file(input_path)
    result = trim(
        env,
        strip_keys=not no_strip_keys,
        strip_values=not no_strip_values,
        normalize_empty=normalize_empty,
    )

    if not quiet:
        print(result.summary(), file=sys.stderr)

    destination = input_path if in_place else output_path
    _write_output(to_dotenv(result.trimmed), destination)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy trim",
        description="Strip whitespace from keys and values in a .env file.",
    )
    p.add_argument("input", help="Path to the .env file to trim.")
    p.add_argument("-o", "--output", default=None, help="Write result to this file.")
    p.add_argument("--in-place", action="store_true", help="Overwrite the input file.")
    p.add_argument("--no-strip-keys", action="store_true", help="Do not strip key whitespace.")
    p.add_argument("--no-strip-values", action="store_true", help="Do not strip value whitespace.")
    p.add_argument("--normalize-empty", action="store_true", help="Replace whitespace-only values with empty string.")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress summary output.")
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    sys.exit(
        run_trim(
            args.input,
            output_path=args.output,
            in_place=args.in_place,
            no_strip_keys=args.no_strip_keys,
            no_strip_values=args.no_strip_values,
            normalize_empty=args.normalize_empty,
            quiet=args.quiet,
        )
    )


if __name__ == "__main__":
    main()
