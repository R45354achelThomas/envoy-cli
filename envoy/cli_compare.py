"""CLI entry-point: envoy compare <base.env> <target.env> [options]."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from envoy.parser import EnvParser, EnvParseError
from envoy.comparator import compare


def _load_env_file(path: str) -> dict:
    try:
        return EnvParser(path).parse()
    except (EnvParseError, OSError) as exc:
        print(f"[error] Could not load {path!r}: {exc}", file=sys.stderr)
        sys.exit(1)


def _load_schema(schema_path: str) -> dict:
    """Load and return a JSON schema from *schema_path*.

    Exits with a non-zero status and prints an error message to stderr if the
    file cannot be read or is not valid JSON.
    """
    import json

    try:
        with open(schema_path) as fh:
            return json.load(fh)
    except OSError as exc:
        print(f"[error] Cannot open schema {schema_path!r}: {exc}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"[error] Schema {schema_path!r} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)


def run_compare(
    base_path: str,
    target_path: str,
    schema_path: Optional[str],
    no_mask: bool,
    include_lint: bool,
    show_diff: bool,
    out=None,
) -> int:
    if out is None:
        out = sys.stdout

    base = _load_env_file(base_path)
    target = _load_env_file(target_path)

    schema = _load_schema(schema_path) if schema_path else None

    report = compare(
        base,
        target,
        base_path=base_path,
        target_path=target_path,
        schema=schema,
        include_lint=include_lint,
        mask_secrets=not no_mask,
    )

    print(report.summary(), file=out)

    if show_diff:
        print("", file=out)
        for entry in report.diff_entries:
            print(f"  [{entry.kind.upper():8s}] {entry.key}", file=out)

    if report.has_lint_errors:
        return 1
    if schema and (
        (report.base_validation and not report.base_validation.is_valid())
        or (report.target_validation and not report.target_validation.is_valid())
    ):
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy compare",
        description="Compare two .env files and report differences.",
    )
    p.add_argument("base", help="Base .env file")
    p.add_argument("target", help="Target .env file")
    p.add_argument("--schema", metavar="FILE", help="JSON schema for validation")
    p.add_argument("--no-mask", action="store_true", help="Show secret values in plain text")
    p.add_argument("--no-lint", action="store_true", help="Skip lint checks")
    p.add_argument("--diff", action="store_true", help="Print per-key diff entries")
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    code = run_compare(
        base_path=args.base,
        target_path=args.target,
        schema_path=args.schema,
        no_mask=args.no_mask,
        include_lint=not args.no_lint,
        show_diff=args.diff,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
