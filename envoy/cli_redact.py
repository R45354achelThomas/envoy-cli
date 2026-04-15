"""CLI entry-point for the redact command."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from envoy.parser import EnvParser
from envoy.redactor import redact, DEFAULT_PLACEHOLDER
from envoy.exporter import to_dotenv


def _load_env_file(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return EnvParser(text).parse()


def run_redact(
    input_path: str,
    output_path: Optional[str] = None,
    placeholder: str = DEFAULT_PLACEHOLDER,
    extra_keys: Optional[List[str]] = None,
    keys_only: Optional[List[str]] = None,
    fmt: str = "dotenv",
    quiet: bool = False,
    out=None,
    err=None,
) -> int:
    out = out or sys.stdout
    err = err or sys.stderr

    try:
        env = _load_env_file(input_path)
    except Exception as exc:
        err.write(f"error: {exc}\n")
        return 1

    result = redact(env, placeholder=placeholder, extra_keys=extra_keys, keys_only=keys_only)

    if fmt == "json":
        rendered = json.dumps(result.redacted, indent=2, sort_keys=True)
    else:
        rendered = to_dotenv(result.redacted)

    if output_path:
        Path(output_path).write_text(rendered, encoding="utf-8")
    else:
        out.write(rendered)
        if not rendered.endswith("\n"):
            out.write("\n")

    if not quiet:
        err.write(result.summary() + "\n")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy redact",
        description="Replace secret values in a .env file with a placeholder.",
    )
    p.add_argument("input", help="Path to the .env file")
    p.add_argument("-o", "--output", metavar="FILE", help="Write result to FILE instead of stdout")
    p.add_argument("-p", "--placeholder", default=DEFAULT_PLACEHOLDER, help="Replacement string")
    p.add_argument("-e", "--extra-keys", nargs="+", metavar="KEY", help="Extra keys to treat as secrets")
    p.add_argument("-k", "--keys-only", nargs="+", metavar="KEY", help="Only redact these keys")
    p.add_argument("--format", choices=["dotenv", "json"], default="dotenv", dest="fmt")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress summary output")
    return p


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(
        run_redact(
            input_path=args.input,
            output_path=args.output,
            placeholder=args.placeholder,
            extra_keys=args.extra_keys,
            keys_only=args.keys_only,
            fmt=args.fmt,
            quiet=args.quiet,
        )
    )


if __name__ == "__main__":
    main()
