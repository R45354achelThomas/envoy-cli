"""CLI entry-point: split a .env file into per-prefix files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from envoy.parser import EnvParser
from envoy.splitter import SplitError, split
from envoy.exporter import to_dotenv


def _load_env_file(path: str) -> dict:
    return EnvParser(Path(path).read_text(encoding="utf-8")).parse()


def run_split(
    input_path: str,
    output_dir: str,
    prefixes: Optional[List[str]] = None,
    separator: str = "_",
    keep_prefix: bool = True,
    include_ungrouped: bool = True,
    stdout: bool = False,
) -> int:
    """Execute the split command.  Returns an exit code."""
    try:
        env = _load_env_file(input_path)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        result = split(env, prefixes=prefixes, separator=separator, keep_prefix=keep_prefix)
    except SplitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if stdout:
        for name, bucket in sorted(result.buckets.items()):
            print(f"# --- {name} ---")
            print(to_dotenv(bucket))
        if include_ungrouped and result.ungrouped:
            print("# --- (ungrouped) ---")
            print(to_dotenv(result.ungrouped))
        return 0

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    written: List[str] = []
    for name, bucket in result.buckets.items():
        dest = out / f"{name.lower()}.env"
        dest.write_text(to_dotenv(bucket), encoding="utf-8")
        written.append(str(dest))

    if include_ungrouped and result.ungrouped:
        dest = out / "ungrouped.env"
        dest.write_text(to_dotenv(result.ungrouped), encoding="utf-8")
        written.append(str(dest))

    print(f"Split into {len(written)} file(s): {', '.join(written)}")
    print(result.summary())
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy split",
        description="Split a .env file into per-prefix files.",
    )
    p.add_argument("input", help="Source .env file")
    p.add_argument("-o", "--output-dir", default=".", help="Directory for output files (default: .)")
    p.add_argument("-p", "--prefix", dest="prefixes", action="append", metavar="PREFIX",
                   help="Prefix to split on (repeatable); auto-detected when omitted")
    p.add_argument("--separator", default="_", help="Prefix/key separator (default: _)")
    p.add_argument("--strip-prefix", dest="keep_prefix", action="store_false",
                   help="Remove the prefix from keys in output files")
    p.add_argument("--no-ungrouped", dest="include_ungrouped", action="store_false",
                   help="Discard keys that don't match any prefix")
    p.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing files")
    return p


def main(argv: Optional[List[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    sys.exit(
        run_split(
            input_path=args.input,
            output_dir=args.output_dir,
            prefixes=args.prefixes,
            separator=args.separator,
            keep_prefix=args.keep_prefix,
            include_ungrouped=args.include_ungrouped,
            stdout=args.stdout,
        )
    )


if __name__ == "__main__":
    main()
