"""CLI entry-point for envoy cast command."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from envoy.parser import EnvParser
from envoy.caster import cast


def _load_env_file(path: str) -> dict:
    return EnvParser(Path(path).read_text(encoding="utf-8")).parse()


def _load_schema(path: str) -> dict:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        print(f"error: schema must be a JSON object", file=sys.stderr)
        sys.exit(2)
    return raw


def run_cast(args: argparse.Namespace, out=sys.stdout) -> int:
    env = _load_env_file(args.env_file)
    schema = _load_schema(args.schema) if args.schema else {}
    result = cast(env, schema)

    if args.format == "json":
        json.dump(result.casted, out, indent=2, default=str)
        out.write("\n")
    else:
        for key, value in result.casted.items():
            out.write(f"{key}={value!r}\n")

    if result.has_failures():
        for key, msg in result.failed.items():
            print(f"warning: {key}: {msg}", file=sys.stderr)

    print(result.summary(), file=sys.stderr)
    return 1 if result.has_failures() else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy cast",
        description="Cast .env values to typed Python values.",
    )
    p.add_argument("env_file", help="Path to .env file")
    p.add_argument("--schema", metavar="FILE", help="JSON schema mapping key -> type")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_cast(args))


if __name__ == "__main__":
    main()
