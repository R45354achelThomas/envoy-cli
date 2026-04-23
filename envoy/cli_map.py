"""CLI entry-point for the ``envoy map`` sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

from envoy.mapper import MapError, map_env
from envoy.parser import EnvParser
from envoy.exporter import to_dotenv


def _load_env_file(path: str) -> Dict[str, str]:
    return EnvParser(Path(path).read_text()).parse()


def _load_mapping(path: str) -> Dict[str, Optional[str]]:
    """Load a JSON mapping file: ``{"OLD_KEY": "NEW_KEY", "DROP_ME": null}``."""
    try:
        raw = json.loads(Path(path).read_text())
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in mapping file: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(raw, dict):
        print("error: mapping file must contain a JSON object", file=sys.stderr)
        sys.exit(2)
    return raw  # type: ignore[return-value]


def run_map(args: argparse.Namespace) -> int:
    try:
        env = _load_env_file(args.env_file)
    except FileNotFoundError:
        print(f"error: file not found: {args.env_file}", file=sys.stderr)
        return 2

    try:
        mapping = _load_mapping(args.mapping)
    except FileNotFoundError:
        print(f"error: mapping file not found: {args.mapping}", file=sys.stderr)
        return 2

    try:
        result = map_env(env, mapping, drop_unmapped=args.drop_unmapped)
    except MapError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = to_dotenv(result.env)

    if args.output:
        Path(args.output).write_text(output)
    else:
        print(output, end="")

    if not args.quiet:
        print(result.summary(), file=sys.stderr)

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy map",
        description="Rename or drop .env keys using a JSON mapping file.",
    )
    p.add_argument("env_file", help="Source .env file")
    p.add_argument("mapping", help="JSON file mapping old keys to new keys (null to drop)")
    p.add_argument("-o", "--output", metavar="FILE", help="Write result to FILE instead of stdout")
    p.add_argument(
        "--drop-unmapped",
        action="store_true",
        default=False,
        help="Exclude keys not present in the mapping",
    )
    p.add_argument("-q", "--quiet", action="store_true", default=False, help="Suppress summary")
    return p


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_map(args))


if __name__ == "__main__":
    main()
