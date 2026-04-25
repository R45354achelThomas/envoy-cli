"""CLI interface for the promote command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from envoy.parser import EnvParser
from envoy.promoter import promote


def _load_env_file(path: str) -> dict:
    return EnvParser(Path(path).read_text(encoding="utf-8")).parse()


def run_promote(
    source: str,
    target: str,
    keys: Optional[List[str]],
    overwrite: bool,
    output: Optional[str],
    stdout=None,
    stderr=None,
) -> int:
    if stdout is None:  # pragma: no cover
        stdout = sys.stdout
    if stderr is None:  # pragma: no cover
        stderr = sys.stderr

    try:
        src_env = _load_env_file(source)
        tgt_env = _load_env_file(target)
    except (OSError, Exception) as exc:
        stderr.write(f"error: {exc}\n")
        return 1

    result = promote(
        src_env,
        tgt_env,
        keys=keys or None,
        overwrite=overwrite,
        source_path=source,
        target_path=target,
    )

    if result.has_conflicts() and not overwrite:
        for key, (src_val, tgt_val) in result.conflicts.items():
            stderr.write(f"conflict: {key!r} src={src_val!r} tgt={tgt_val!r}\n")

    stdout.write(f"Summary: {result.summary()}\n")

    if output:
        merged = dict(tgt_env)
        merged.update(result.promoted)
        lines = [f"{k}={v}\n" for k, v in merged.items()]
        Path(output).write_text("".join(lines), encoding="utf-8")
        stdout.write(f"Written to {output}\n")

    return 1 if (result.has_conflicts() and not overwrite) else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy promote",
        description="Promote env vars from a source file into a target file.",
    )
    p.add_argument("source", help="Source .env file (e.g. .env.production)")
    p.add_argument("target", help="Target .env file (e.g. .env.staging)")
    p.add_argument("-k", "--keys", nargs="+", metavar="KEY", help="Keys to promote (default: all)")
    p.add_argument("--overwrite", action="store_true", help="Overwrite conflicting keys in target")
    p.add_argument("-o", "--output", metavar="FILE", help="Write merged result to FILE")
    return p


def main(argv=None) -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_promote(args.source, args.target, args.keys, args.overwrite, args.output))
