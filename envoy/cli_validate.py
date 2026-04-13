"""CLI entry point for validating a .env file against a schema/template."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.parser import EnvParser
from envoy.validator import validate


def _load_env_file(path: str) -> dict[str, str]:
    """Parse an env file and return its key/value pairs."""
    text = Path(path).read_text(encoding="utf-8")
    parser = EnvParser(text)
    return dict(parser.parse())


def run_validate(
    env_path: str,
    schema_path: str,
    strict: bool = False,
    *,
    output=None,
) -> int:
    """Validate *env_path* against *schema_path*.

    Returns an exit code: 0 = OK, 1 = errors/warnings found.
    """
    if output is None:
        output = sys.stdout

    env = _load_env_file(env_path)
    schema = _load_env_file(schema_path)

    result = validate(env, schema, strict=strict)

    if result.is_valid and not result.warnings:
        output.write(f"OK  {env_path} is valid against {schema_path}\n")
        return 0

    for line in result.summary().splitlines():
        output.write(line + "\n")

    return 0 if result.is_valid else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy validate",
        description="Validate a .env file against a schema (template) file.",
    )
    p.add_argument("env", help="Path to the .env file to validate.")
    p.add_argument("schema", help="Path to the schema / template .env file.")
    p.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Treat extra keys in the env file as errors.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_validate(args.env, args.schema, strict=args.strict))


if __name__ == "__main__":  # pragma: no cover
    main()
