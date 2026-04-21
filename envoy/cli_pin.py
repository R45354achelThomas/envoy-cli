"""CLI entry-point for the pin / drift-detection command."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

from envoy.parser import EnvParser
from envoy.pinner import PinError, pin


def _load_env_file(path: str) -> Dict[str, str]:
    text = Path(path).read_text(encoding="utf-8")
    return EnvParser(text).parse()


def run_pin(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        env = _load_env_file(args.env_file)
    except (OSError, Exception) as exc:
        err.write(f"error: {exc}\n")
        return 1

    existing_pin: dict | None = None
    if args.pin_file and Path(args.pin_file).exists():
        try:
            existing_pin = json.loads(Path(args.pin_file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            err.write(f"error reading pin file: {exc}\n")
            return 1

    keys = args.keys if args.keys else None

    try:
        result = pin(env, existing_pin=existing_pin, keys=keys)
    except PinError as exc:
        err.write(f"pin error: {exc}\n")
        return 1

    if existing_pin is None:
        # Write a new pin file
        dest = args.pin_file or "envoy.pin.json"
        Path(dest).write_text(json.dumps(result.pinned, indent=2, sort_keys=True), encoding="utf-8")
        out.write(f"Pinned {len(result.pinned)} keys to {dest}\n")
        return 0

    # Report drift
    out.write(f"Summary: {result.summary()}\n")
    for k in result.drifted:
        out.write(f"  DRIFTED  {k}\n")
    for k in result.missing:
        out.write(f"  MISSING  {k}\n")
    for k in result.new_keys:
        out.write(f"  NEW      {k}\n")

    return 1 if result.has_drift() else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy pin",
        description="Pin env values and detect drift against a saved pin.",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument("--pin-file", metavar="PATH", default="envoy.pin.json",
                   help="Path to the JSON pin file (default: envoy.pin.json)")
    p.add_argument("--keys", nargs="+", metavar="KEY",
                   help="Restrict pinning/comparison to these keys")
    return p


def main(argv=None):
    sys.exit(run_pin(build_parser().parse_args(argv)))


if __name__ == "__main__":
    main()
