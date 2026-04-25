"""CLI entry-point for the `envoy link` command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

from envoy.linker import LinkError, link
from envoy.parser import EnvParser


def _load_env_file(path: str) -> Dict[str, str]:
    text = Path(path).read_text(encoding="utf-8")
    return EnvParser(text).parse()


def run_link(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    if len(args.files) < 2:
        err.write("error: at least two .env files are required\n")
        return 2

    envs: Dict[str, Dict[str, str]] = {}
    for path in args.files:
        try:
            envs[path] = _load_env_file(path)
        except (OSError, Exception) as exc:
            err.write(f"error: cannot load {path!r}: {exc}\n")
            return 1

    try:
        result = link(envs)
    except LinkError as exc:
        err.write(f"error: {exc}\n")
        return 1

    if args.format == "summary":
        out.write(result.summary() + "\n")
        return 0

    # default: text report
    if result.shared:
        out.write(f"Shared keys ({len(result.shared)}):\n")
        for key, sources in sorted(result.shared.items()):
            out.write(f"  {key}  [{', '.join(sources)}]\n")
    else:
        out.write("No shared keys.\n")

    if result.unique:
        out.write(f"\nUnique keys ({len(result.unique)}):\n")
        for key, source in sorted(result.unique.items()):
            out.write(f"  {key}  [{source}]\n")
    else:
        out.write("\nNo unique keys.\n")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy link",
        description="Cross-reference keys across multiple .env files.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Two or more .env files to compare.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "summary"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def main(argv=None) -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_link(args))
