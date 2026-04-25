"""CLI entry point for the `envoy stage` command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from envoy.parser import EnvParser
from envoy.stager import stage
from envoy.exporter import to_dotenv


def _load_env_file(path: str) -> dict:
    parser = EnvParser()
    return parser.parse(Path(path).read_text(encoding="utf-8"))


def run_stage(
    source_path: str,
    target_path: str,
    keys: Optional[List[str]],
    *,
    overwrite: bool = True,
    output: Optional[str] = None,
    in_place: bool = False,
    stdout=None,
    stderr=None,
) -> int:
    if stdout is None:  # pragma: no cover
        stdout = sys.stdout
    if stderr is None:  # pragma: no cover
        stderr = sys.stderr

    try:
        source = _load_env_file(source_path)
        target = _load_env_file(target_path)
    except Exception as exc:  # noqa: BLE001
        stderr.write(f"Error loading env file: {exc}\n")
        return 1

    result = stage(
        source,
        target,
        keys=keys,
        overwrite=overwrite,
        source_env=source_path,
        target_env=target_path,
    )

    stdout.write(result.summary() + "\n")

    dotenv_output = to_dotenv(result.staged)

    dest = output or (target_path if in_place else None)
    if dest:
        Path(dest).write_text(dotenv_output, encoding="utf-8")
    else:
        stdout.write(dotenv_output)

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy stage",
        description="Stage env vars from a source file into a target file.",
    )
    p.add_argument("source", help="Source .env file to pull values from.")
    p.add_argument("target", help="Target .env file to push values into.")
    p.add_argument(
        "--keys", nargs="+", metavar="KEY",
        help="Specific keys to stage (default: all source keys).",
    )
    p.add_argument(
        "--no-overwrite", dest="overwrite", action="store_false", default=True,
        help="Skip keys that already exist in the target.",
    )
    p.add_argument("--output", "-o", metavar="FILE", help="Write result to FILE.")
    p.add_argument(
        "--in-place", action="store_true",
        help="Overwrite the target file in place.",
    )
    return p


def main(argv=None) -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(
        run_stage(
            args.source,
            args.target,
            keys=args.keys,
            overwrite=args.overwrite,
            output=args.output,
            in_place=args.in_place,
        )
    )
