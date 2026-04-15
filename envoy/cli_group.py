"""CLI entry-point for the `envoy group` subcommand."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Dict

from envoy.parser import EnvParser
from envoy.grouper import GroupError, group


def _load_env_file(path: str) -> Dict[str, str]:
    with open(path, "r", encoding="utf-8") as fh:
        return EnvParser(fh.read()).parse()


def run_group(
    env_path: str,
    *,
    separator: str = "_",
    prefix_map_path: str | None = None,
    output_format: str = "text",
    show_ungrouped: bool = True,
    out=None,
    err=None,
) -> int:
    out = out or sys.stdout
    err = err or sys.stderr

    try:
        env = _load_env_file(env_path)
    except (OSError, Exception) as exc:
        print(f"error: {exc}", file=err)
        return 1

    prefix_map = None
    if prefix_map_path:
        try:
            with open(prefix_map_path, "r", encoding="utf-8") as fh:
                prefix_map = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error loading prefix map: {exc}", file=err)
            return 1

    try:
        result = group(env, separator=separator, prefix_map=prefix_map)
    except GroupError as exc:
        print(f"error: {exc}", file=err)
        return 1

    if output_format == "json":
        payload = {"groups": result.groups}
        if show_ungrouped:
            payload["ungrouped"] = result.ungrouped
        print(json.dumps(payload, indent=2, sort_keys=True), file=out)
    else:
        for name in result.group_names():
            print(f"[{name}]", file=out)
            for k, v in sorted(result.groups[name].items()):
                print(f"  {k}={v}", file=out)
        if show_ungrouped and result.has_ungrouped():
            print("[ungrouped]", file=out)
            for k, v in sorted(result.ungrouped.items()):
                print(f"  {k}={v}", file=out)

    print(result.summary(), file=err)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy group",
        description="Group env keys by prefix.",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument("--separator", default="_", help="Key segment separator (default: _)")
    p.add_argument("--prefix-map", dest="prefix_map", metavar="FILE",
                   help="JSON file mapping prefixes to group names")
    p.add_argument("--format", dest="output_format", choices=["text", "json"], default="text")
    p.add_argument("--no-ungrouped", dest="show_ungrouped", action="store_false",
                   help="Omit ungrouped keys from output")
    return p


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(
        run_group(
            args.env_file,
            separator=args.separator,
            prefix_map_path=args.prefix_map,
            output_format=args.output_format,
            show_ungrouped=args.show_ungrouped,
        )
    )


if __name__ == "__main__":
    main()
