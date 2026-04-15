"""CLI entry-point for the flatten command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from envoy.flattener import FlattenError, flatten
from envoy.parser import EnvParser
from envoy.exporter import to_dotenv, to_json, to_shell


def _load_env_file(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return EnvParser(text).parse()


def run_flatten(
    input_path: str,
    separator: str = "__",
    strip_prefix: Optional[str] = None,
    lowercase: bool = False,
    collision: str = "skip",
    output_format: str = "dotenv",
    output_path: Optional[str] = None,
    quiet: bool = False,
    out=None,
    err=None,
) -> int:
    out = out or sys.stdout
    err = err or sys.stderr

    try:
        env = _load_env_file(input_path)
    except (OSError, Exception) as exc:
        err.write(f"Error loading {input_path!r}: {exc}\n")
        return 1

    try:
        result = flatten(
            env,
            separator=separator,
            strip_prefix=strip_prefix,
            lowercase=lowercase,
            collision=collision,
        )
    except FlattenError as exc:
        err.write(f"Flatten error: {exc}\n")
        return 1

    if not quiet:
        err.write(result.summary() + "\n")

    if output_format == "json":
        text = to_json(result.flattened)
    elif output_format == "shell":
        text = to_shell(result.flattened)
    else:
        text = to_dotenv(result.flattened)

    if output_path:
        Path(output_path).write_text(text, encoding="utf-8")
    else:
        out.write(text)
        if not text.endswith("\n"):
            out.write("\n")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy flatten",
        description="Flatten nested env keys by collapsing a separator.",
    )
    p.add_argument("input", help="Path to the .env file")
    p.add_argument("--separator", default="__", help="Segment separator (default: '__')")
    p.add_argument("--strip-prefix", default=None, help="Remove this prefix from keys")
    p.add_argument("--lowercase", action="store_true", help="Lowercase output keys")
    p.add_argument("--collision", choices=["skip", "overwrite"], default="skip")
    p.add_argument("--format", dest="output_format", choices=["dotenv", "json", "shell"], default="dotenv")
    p.add_argument("--output", dest="output_path", default=None, help="Write to file instead of stdout")
    p.add_argument("--quiet", action="store_true", help="Suppress summary output")
    return p


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(
        run_flatten(
            input_path=args.input,
            separator=args.separator,
            strip_prefix=args.strip_prefix,
            lowercase=args.lowercase,
            collision=args.collision,
            output_format=args.output_format,
            output_path=args.output_path,
            quiet=args.quiet,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
