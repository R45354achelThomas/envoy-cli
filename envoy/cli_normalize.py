"""CLI entry-point for the normalize command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from envoy.normalizer import NormalizeError, normalize
from envoy.parser import EnvParser
from envoy.exporter import to_dotenv


def _load_env_file(path: str) -> dict:
    parser = EnvParser(Path(path).read_text(encoding="utf-8"))
    return dict(parser.parse())


def _write_output(data: dict, dest: Optional[str]) -> None:
    content = to_dotenv(data)
    if dest:
        Path(dest).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)


def run_normalize(
    input_path: str,
    output_path: Optional[str] = None,
    *,
    no_uppercase: bool = False,
    no_strip: bool = False,
    no_replace_spaces: bool = False,
    quiet: bool = False,
) -> int:
    """Normalize *input_path* and write result; return exit code."""
    try:
        env = _load_env_file(input_path)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        result = normalize(
            env,
            uppercase_keys=not no_uppercase,
            strip_values=not no_strip,
            replace_spaces_in_keys=not no_replace_spaces,
        )
    except NormalizeError as exc:
        print(f"normalize error: {exc}", file=sys.stderr)
        return 1

    _write_output(result.normalized, output_path)

    if not quiet:
        print(result.summary(), file=sys.stderr)

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy normalize",
        description="Normalize keys and values in a .env file.",
    )
    p.add_argument("input", help="Path to the source .env file")
    p.add_argument("-o", "--output", metavar="FILE", help="Write output to FILE instead of stdout")
    p.add_argument("--no-uppercase", action="store_true", help="Do not uppercase keys")
    p.add_argument("--no-strip", action="store_true", help="Do not strip value whitespace")
    p.add_argument("--no-replace-spaces", action="store_true", help="Do not replace spaces in keys")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress summary output")
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    sys.exit(
        run_normalize(
            args.input,
            args.output,
            no_uppercase=args.no_uppercase,
            no_strip=args.no_strip,
            no_replace_spaces=args.no_replace_spaces,
            quiet=args.quiet,
        )
    )


if __name__ == "__main__":
    main()
