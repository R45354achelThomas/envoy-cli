"""CLI command handler for the `envoy merge` subcommand."""

import sys
from pathlib import Path
from typing import List, Optional

from envoy.parser import parse_env_string, EnvParseError
from envoy.merger import merge_envs


def _load_env_file(path: str) -> dict:
    """Read and parse a .env file, raising SystemExit on failure."""
    p = Path(path)
    if not p.exists():
        print(f"[error] File not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        return parse_env_string(p.read_text(encoding="utf-8"))
    except EnvParseError as exc:
        print(f"[error] Failed to parse '{path}': {exc}", file=sys.stderr)
        sys.exit(1)


def run_merge(
    files: List[str],
    output: Optional[str] = None,
    override: bool = False,
    ignore_conflicts: bool = False,
    quiet: bool = False,
) -> int:
    """Entry point for the merge command.

    Args:
        files: Ordered list of .env file paths to merge.
        output: Optional path to write the merged result.
        override: If True, later files override earlier ones.
        ignore_conflicts: If True, suppress conflict detection.
        quiet: Suppress informational output.

    Returns:
        Exit code (0 = success, 1 = conflicts detected).
    """
    if len(files) < 2:
        print("[error] At least two files are required for merging.", file=sys.stderr)
        return 1

    sources = [(f, _load_env_file(f)) for f in files]
    result = merge_envs(sources, override=override, ignore_conflicts=ignore_conflicts)

    if not quiet:
        print(result.summary())

    if result.has_conflicts and not ignore_conflicts:
        if not quiet:
            print("\n[!] Resolve conflicts before writing output.", file=sys.stderr)
        return 1

    merged_lines = [f"{k}={v}" for k, v in sorted(result.merged.items())]
    merged_content = "\n".join(merged_lines) + "\n"

    if output:
        Path(output).write_text(merged_content, encoding="utf-8")
        if not quiet:
            print(f"\nMerged env written to: {output}")
    else:
        print("\n" + merged_content)

    return 0
