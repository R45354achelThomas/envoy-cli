"""CLI entry-point for the import subcommand."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from envoy.importer import ImportError, from_dotenv_text, from_json, from_shell
from envoy.exporter import to_dotenv


def _write_output(env: dict, output: Optional[str]) -> None:
    text = to_dotenv(env)
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def run_import(args: argparse.Namespace) -> int:
    keys: Optional[List[str]] = args.keys or None

    try:
        if args.source == "shell":
            result = from_shell(
                keys=keys,
                prefix=args.prefix or None,
                strip_prefix=args.strip_prefix,
            )
        elif args.source == "json":
            if not args.file:
                print("error: --file is required for json source", file=sys.stderr)
                return 2
            text = Path(args.file).read_text(encoding="utf-8")
            result = from_json(text, keys=keys)
        elif args.source == "dotenv":
            if not args.file:
                print("error: --file is required for dotenv source", file=sys.stderr)
                return 2
            text = Path(args.file).read_text(encoding="utf-8")
            result = from_dotenv_text(text, keys=keys)
        else:
            print(f"error: unknown source '{args.source}'", file=sys.stderr)
            return 2
    except (ImportError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _write_output(result.env, getattr(args, "output", None))

    if not args.quiet:
        print(result.summary(), file=sys.stderr)

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy import",
        description="Import env vars from shell, JSON, or a .env file.",
    )
    p.add_argument(
        "source",
        choices=["shell", "json", "dotenv"],
        help="Source type to import from.",
    )
    p.add_argument("--file", "-f", help="Input file path (required for json/dotenv).")
    p.add_argument("--output", "-o", help="Write result to file instead of stdout.")
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Only import these specific keys.",
    )
    p.add_argument("--prefix", help="Filter shell vars by this prefix (shell source only).")
    p.add_argument(
        "--strip-prefix",
        action="store_true",
        default=False,
        help="Remove prefix from key names after filtering.",
    )
    p.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Suppress summary output.",
    )
    return p


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_import(args))


if __name__ == "__main__":
    main()
