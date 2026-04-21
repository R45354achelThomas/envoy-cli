"""CLI entry-point for the 'classify' command."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from envoy.classifier import classify
from envoy.parser import EnvParser


def _load_env_file(path: str) -> dict:
    return EnvParser(Path(path).read_text(encoding="utf-8")).parse()


def run_classify(
    env_path: str,
    fmt: str = "text",
    category_filter: Optional[List[str]] = None,
    output: Optional[str] = None,
) -> int:
    """Classify keys in *env_path* and print/write results.

    Returns an exit code (0 = success).
    """
    env = _load_env_file(env_path)
    result = classify(env)

    if fmt == "json":
        data = {
            cat: list(keys.keys())
            for cat, keys in sorted(result.categories.items())
            if not category_filter or cat in category_filter
        }
        text = json.dumps(data, indent=2)
    else:
        lines: List[str] = []
        for cat, entries in sorted(result.categories.items()):
            if category_filter and cat not in category_filter:
                continue
            lines.append(f"[{cat}]")
            for key in sorted(entries):
                lines.append(f"  {key}")
        text = "\n".join(lines) if lines else "(no keys matched)"

    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy classify",
        description="Classify .env keys into semantic categories.",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--category",
        metavar="NAME",
        action="append",
        dest="category_filter",
        help="Show only this category (repeatable)",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    return p


def main(argv: Optional[List[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    sys.exit(
        run_classify(
            env_path=args.env_file,
            fmt=args.fmt,
            category_filter=args.category_filter,
            output=args.output,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
