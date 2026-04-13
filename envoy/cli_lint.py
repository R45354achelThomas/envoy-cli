"""CLI entry-point for the lint sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.linter import lint


def _read_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(2)
    except OSError as exc:
        print(f"Error reading {path}: {exc}", file=sys.stderr)
        sys.exit(2)


def run_lint(
    env_path: str,
    *,
    show_warnings: bool = True,
    strict: bool = False,
    output=None,
) -> int:
    """Run the linter and return an exit code (0 = ok, 1 = issues found)."""
    if output is None:
        output = sys.stdout

    source = _read_file(env_path)
    result = lint(source)

    for issue in result.issues:
        if issue.severity == "error" or show_warnings:
            print(str(issue), file=output)

    print(result.summary(), file=output)

    if result.has_errors:
        return 1
    if strict and result.has_issues:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy lint",
        description="Lint a .env file for style and convention issues.",
    )
    parser.add_argument("env_file", help="Path to the .env file to lint.")
    parser.add_argument(
        "--no-warnings",
        action="store_true",
        default=False,
        help="Suppress warning-level issues; only show errors.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with code 1 even if only warnings are present.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    code = run_lint(
        args.env_file,
        show_warnings=not args.no_warnings,
        strict=args.strict,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
