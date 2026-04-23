"""CLI entry-point for the mask command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from envoy.parser import EnvParser
from envoy.masker import MaskError, mask
from envoy.exporter import to_dotenv


def _load_env_file(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return EnvParser().parse(text)


def run_mask(
    input_path: str,
    *,
    keys: Optional[List[str]] = None,
    placeholder: str = "***",
    auto_detect: bool = True,
    output_path: Optional[str] = None,
    show_summary: bool = True,
    stdout=None,
    stderr=None,
) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    try:
        env = _load_env_file(input_path)
    except (OSError, Exception) as exc:
        stderr.write(f"error: {exc}\n")
        return 1

    try:
        result = mask(env, keys=keys, placeholder=placeholder, auto_detect=auto_detect)
    except MaskError as exc:
        stderr.write(f"mask error: {exc}\n")
        return 1

    dotenv_text = to_dotenv(result.masked)

    if output_path:
        Path(output_path).write_text(dotenv_text, encoding="utf-8")
    else:
        stdout.write(dotenv_text)
        if not dotenv_text.endswith("\n"):
            stdout.write("\n")

    if show_summary:
        stderr.write(result.summary() + "\n")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy mask",
        description="Mask sensitive values in a .env file.",
    )
    p.add_argument("input", help="Path to the .env file")
    p.add_argument("-o", "--output", metavar="FILE", help="Write masked output to FILE")
    p.add_argument("-k", "--key", dest="keys", action="append", metavar="KEY",
                   help="Additional key to mask (repeatable)")
    p.add_argument("--placeholder", default="***", help="Replacement text (default: ***)")
    p.add_argument("--no-auto-detect", dest="auto_detect", action="store_false",
                   help="Disable automatic secret-key detection")
    p.add_argument("--no-summary", dest="show_summary", action="store_false",
                   help="Suppress the summary line")
    return p


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(
        run_mask(
            args.input,
            keys=args.keys,
            placeholder=args.placeholder,
            auto_detect=args.auto_detect,
            output_path=args.output,
            show_summary=args.show_summary,
        )
    )


if __name__ == "__main__":
    main()
