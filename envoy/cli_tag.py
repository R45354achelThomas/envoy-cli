"""CLI interface for the tagger module."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

from envoy.parser import EnvParser
from envoy.tagger import TagError, tag


def _load_env_file(path: str) -> Dict[str, str]:
    text = Path(path).read_text(encoding="utf-8")
    return EnvParser(text).parse()


def _parse_tag_args(assignments: List[str]) -> Dict[str, List[str]]:
    """Parse KEY=tag1,tag2 strings into a tag_map dict."""
    tag_map: Dict[str, List[str]] = {}
    for item in assignments:
        if "=" not in item:
            raise ValueError(f"Invalid tag assignment (expected KEY=tag1,tag2): {item!r}")
        key, _, labels_str = item.partition("=")
        labels = [lbl.strip() for lbl in labels_str.split(",") if lbl.strip()]
        if not labels:
            raise ValueError(f"No labels provided for key {key!r}")
        tag_map[key] = labels
    return tag_map


def run_tag(
    env_path: str,
    assignments: List[str],
    *,
    filter_tag: str | None = None,
    strict: bool = False,
    output_json: bool = False,
    out: object = sys.stdout,
) -> int:
    try:
        env = _load_env_file(env_path)
    except FileNotFoundError:
        print(f"Error: file not found: {env_path}", file=sys.stderr)
        return 1

    try:
        tag_map = _parse_tag_args(assignments)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        result = tag(env, tag_map, ignore_missing=not strict)
    except TagError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if filter_tag:
        keys = result.keys_for_tag(filter_tag)
        if output_json:
            json.dump({k: env[k] for k in keys if k in env}, out, indent=2)
            print(file=out)
        else:
            print(f"Keys tagged '{filter_tag}':", file=out)
            for key in keys:
                print(f"  {key}", file=out)
    else:
        if output_json:
            json.dump({k: sorted(v) for k, v in result.tags.items()}, out, indent=2)
            print(file=out)
        else:
            print(result.summary(), file=out)
            for key, labels in sorted(result.tags.items()):
                print(f"  {key}: {', '.join(sorted(labels))}", file=out)

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy tag",
        description="Tag .env keys with arbitrary labels.",
    )
    p.add_argument("env_file", help="Path to the .env file.")
    p.add_argument("tags", nargs="+", metavar="KEY=tag1,tag2", help="Tag assignments.")
    p.add_argument("--filter", dest="filter_tag", metavar="TAG", help="Show only keys with this tag.")
    p.add_argument("--strict", action="store_true", help="Error on missing keys.")
    p.add_argument("--json", dest="output_json", action="store_true", help="Output as JSON.")
    return p


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(
        run_tag(
            args.env_file,
            args.tags,
            filter_tag=args.filter_tag,
            strict=args.strict,
            output_json=args.output_json,
        )
    )


if __name__ == "__main__":
    main()
