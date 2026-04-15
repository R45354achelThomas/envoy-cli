"""CLI entry-point for the extract sub-command."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from envoy.extractor import ExtractError, extract
from envoy.parser import EnvParser
from envoy.exporter import to_dotenv, to_json, to_shell


def _load_env_file(path: str) -> dict:
    return EnvParser(Path(path).read_text(encoding="utf-8")).parse()


def run_extract(
    source: str,
    keys: List[str],
    *,
    allow_missing: bool = False,
    default: Optional[str] = None,
    fmt: str = "dotenv",
    output: Optional[str] = None,
    stdout=None,
    stderr=None,
) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    try:
        env = _load_env_file(source)
    except (OSError, Exception) as exc:
        stderr.write(f"error: cannot load {source!r}: {exc}\n")
        return 1

    try:
        result = extract(env, keys, allow_missing=allow_missing, default=default)
    except ExtractError as exc:
        stderr.write(f"error: {exc}\n")
        return 1

    if result.missing and not allow_missing and default is None:
        stderr.write(f"warning: {len(result.missing)} key(s) not found\n")

    formatters = {"dotenv": to_dotenv, "json": to_json, "shell": to_shell}
    formatter = formatters.get(fmt, to_dotenv)
    text = formatter(result.extracted)

    if output:
        Path(output).write_text(text, encoding="utf-8")
        stderr.write(f"written to {output}\n")
    else:
        stdout.write(text)
        if not text.endswith("\n"):
            stdout.write("\n")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy extract",
        description="Extract specific keys from an env file.",
    )
    p.add_argument("source", help="Source .env file")
    p.add_argument("keys", nargs="+", help="Keys to extract")
    p.add_argument("--allow-missing", action="store_true", help="Skip absent keys instead of failing")
    p.add_argument("--default", metavar="VALUE", help="Default value for absent keys")
    p.add_argument("--format", dest="fmt", choices=["dotenv", "json", "shell"], default="dotenv")
    p.add_argument("--output", "-o", metavar="FILE", help="Write output to FILE")
    return p


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(
        run_extract(
            args.source,
            args.keys,
            allow_missing=args.allow_missing,
            default=args.default,
            fmt=args.fmt,
            output=args.output,
        )
    )


if __name__ == "__main__":
    main()
