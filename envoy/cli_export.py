"""CLI entry point for the `envoy export` subcommand."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from envoy.parser import parse_env_file, EnvParseError
from envoy.exporter import export_env, ExportError, ExportFormat


def _load_env_file(path: str) -> dict:
    """Load and parse a .env file, exiting on error."""
    try:
        return parse_env_file(Path(path))
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except EnvParseError as exc:
        print(f"Error parsing {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def run_export(
    env_file: str,
    fmt: ExportFormat = "dotenv",
    output: Optional[str] = None,
) -> None:
    """
    Export an .env file to the specified format.

    Args:
        env_file: Path to the source .env file.
        fmt: Target format — 'shell', 'json', 'yaml', or 'dotenv'.
        output: Optional output file path; prints to stdout if None.
    """
    env = _load_env_file(env_file)

    try:
        result = export_env(env, fmt)
    except ExportError as exc:
        print(f"Export error: {exc}", file=sys.stderr)
        sys.exit(1)

    if output:
        try:
            Path(output).write_text(result + "\n", encoding="utf-8")
            print(f"Exported {len(env)} variable(s) to {output} [{fmt}]")
        except OSError as exc:
            print(f"Error writing to {output}: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        print(result)
