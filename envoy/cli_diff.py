"""CLI entry point for diffing two .env files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.diff import compute_diff, format_diff
from envoy.parser import EnvParser, EnvParseError


def _load_env_file(path: str) -> dict[str, str]:
    """Parse an .env file and return key/value pairs.

    Args:
        path: Filesystem path to the .env file.

    Returns:
        A dictionary mapping variable names to their values.

    Raises:
        SystemExit: If the file is not found or cannot be parsed.
    """
    try:
        return EnvParser(Path(path).read_text(encoding="utf-8")).parse()
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"error: permission denied: {path}", file=sys.stderr)
        sys.exit(1)
    except EnvParseError as exc:
        print(f"error: could not parse {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def run_diff(
    old_path: str,
    new_path: str,
    *,
    show_unchanged: bool = False,
    mask_secrets: bool = True,
    output_file: str | None = None,
    exit_nonzero: bool = False,
) -> None:
    """Compute and display the diff between two .env files."""
    old_env = _load_env_file(old_path)
    new_env = _load_env_file(new_path)

    entries = compute_diff(old_env, new_env, include_unchanged=show_unchanged)
    output = format_diff(entries, mask_secrets=mask_secrets)

    if output_file:
        try:
            Path(output_file).write_text(output, encoding="utf-8")
        except PermissionError:
            print(f"error: permission denied writing to: {output_file}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output, end="")

    if exit_nonzero and any(e.status != "unchanged" for e in entries):
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy diff",
        description="Show differences between two .env files.",
    )
    p.add_argument("old", help="Path to the old/base .env file")
    p.add_argument("new", help="Path to the new .env file")
    p.add_argument(
        "--show-unchanged",
        action="store_true",
        default=False,
        help="Include unchanged keys in the output",
    )
    p.add_argument(
        "--no-mask",
        action="store_true",
        default=False,
        help="Do not mask secret values",
    )
    p.add_argument(
        "--output", "-o",
        metavar="FILE",
        default=None,
        help="Write diff output to FILE instead of stdout",
    )
    p.add_argument(
        "--exit-nonzero",
        action="store_true",
        default=False,
        help="Exit with code 1 if any differences are found",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_diff(
        args.old,
        args.new,
        show_unchanged=args.show_unchanged,
        mask_secrets=not args.no_mask,
        output_file=args.output,
        exit_nonzero=args.exit_nonzero,
    )
