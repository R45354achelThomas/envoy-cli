"""CLI entry-point for the `envoy filter` command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from envoy.filter import FilterError, filter_env
from envoy.parser import EnvParser


def _load_env_file(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return EnvParser(text).parse()


def run_filter(
    env_path: str,
    pattern: Optional[str] = None,
    prefix: Optional[str] = None,
    exclude_empty: bool = False,
    invert: bool = False,
    show_excluded: bool = False,
    output: Optional[str] = None,
    out=None,
    err=None,
) -> int:
    if out is None:
        out = sys.stdout
    if err is None:
        err = sys.stderr

    try:
        env = _load_env_file(env_path)
    except (OSError, Exception) as exc:
        err.write(f"Error loading {env_path!r}: {exc}\n")
        return 1

    try:
        result = filter_env(
            env,
            pattern=pattern,
            prefix=prefix,
            exclude_empty=exclude_empty,
            invert=invert,
        )
    except FilterError as exc:
        err.write(f"Filter error: {exc}\n")
        return 1

    target = result.excluded if show_excluded else result.matched
    lines = [f"{k}={v}" for k, v in target.items()]
    content = "\n".join(lines) + ("\n" if lines else "")

    if output:
        Path(output).write_text(content, encoding="utf-8")
        out.write(result.summary() + "\n")
    else:
        out.write(content)

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy filter",
        description="Filter .env keys by pattern, prefix, or value presence.",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument("--pattern", "-p", help="Regex pattern matched against key names")
    p.add_argument("--prefix", help="Keep only keys starting with this prefix")
    p.add_argument("--exclude-empty", action="store_true", help="Drop keys with empty values")
    p.add_argument("--invert", action="store_true", help="Invert the filter (show excluded set)")
    p.add_argument("--show-excluded", action="store_true", help="Output excluded keys instead")
    p.add_argument("--output", "-o", help="Write result to file instead of stdout")
    return p


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(
        run_filter(
            args.env_file,
            pattern=args.pattern,
            prefix=args.prefix,
            exclude_empty=args.exclude_empty,
            invert=args.invert,
            show_excluded=args.show_excluded,
            output=args.output,
        )
    )


if __name__ == "__main__":
    main()
