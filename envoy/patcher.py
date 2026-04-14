"""Apply a set of key/value patches to an existing .env file in-place."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class PatchError(Exception):
    """Raised when a patch operation cannot be completed."""


@dataclass
class PatchResult:
    applied: Dict[str, str] = field(default_factory=dict)   # key -> new value
    added: Dict[str, str] = field(default_factory=dict)     # brand-new keys
    skipped: List[str] = field(default_factory=list)        # keys not in patch

    @property
    def has_changes(self) -> bool:
        return bool(self.applied or self.added)

    def summary(self) -> str:
        parts = []
        if self.applied:
            parts.append(f"{len(self.applied)} updated")
        if self.added:
            parts.append(f"{len(self.added)} added")
        if not parts:
            return "No changes applied."
        return ", ".join(parts) + "."


_KEY_LINE_RE = re.compile(
    r'^(?P<key>[A-Za-z_][A-Za-z0-9_]*)(?P<sep>\s*=\s*)(?P<rest>.*)$'
)


def _quote_if_needed(value: str) -> str:
    """Wrap value in double quotes if it contains spaces or special chars."""
    if any(c in value for c in (' ', '\t', '#', '"', "'")):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value


def patch(
    source: str,
    patches: Dict[str, str],
    *,
    add_missing: bool = True,
    preserve_quotes: bool = False,
) -> tuple[str, PatchResult]:
    """Apply *patches* to the .env *source* text.

    Parameters
    ----------
    source:         Raw text of the .env file.
    patches:        Mapping of key -> new value to apply.
    add_missing:    When True, keys absent from the file are appended.
    preserve_quotes: When True, keep the original quoting style for updated lines.

    Returns
    -------
    (new_source, PatchResult)
    """
    remaining = dict(patches)
    result = PatchResult()
    out_lines: List[str] = []

    for line in source.splitlines(keepends=True):
        stripped = line.rstrip('\n').rstrip('\r')
        m = _KEY_LINE_RE.match(stripped)
        if m and m.group('key') in remaining:
            key = m.group('key')
            new_val = remaining.pop(key)
            if preserve_quotes:
                # keep original quoting style — just replace value portion
                old_rest = m.group('rest')
                quote_char: Optional[str] = None
                if old_rest.startswith('"'):
                    quote_char = '"'
                elif old_rest.startswith("'"):
                    quote_char = "'"
                if quote_char:
                    escaped = new_val.replace(quote_char, f'\\{quote_char}')
                    formatted = f'{key}{m.group("sep")}{quote_char}{escaped}{quote_char}'
                else:
                    formatted = f'{key}{m.group("sep")}{_quote_if_needed(new_val)}'
            else:
                formatted = f'{key}={_quote_if_needed(new_val)}'
            eol = '\n' if line.endswith('\n') else ''
            out_lines.append(formatted + eol)
            result.applied[key] = new_val
        else:
            out_lines.append(line)

    if add_missing and remaining:
        if out_lines and not out_lines[-1].endswith('\n'):
            out_lines.append('\n')
        for key, value in remaining.items():
            out_lines.append(f'{key}={_quote_if_needed(value)}\n')
            result.added[key] = value

    return ''.join(out_lines), result


def patch_file(
    path: Path,
    patches: Dict[str, str],
    *,
    add_missing: bool = True,
    preserve_quotes: bool = False,
) -> PatchResult:
    """Read *path*, apply patches, and write back in-place."""
    try:
        source = path.read_text(encoding='utf-8')
    except OSError as exc:
        raise PatchError(f"Cannot read {path}: {exc}") from exc

    new_source, result = patch(
        source, patches, add_missing=add_missing, preserve_quotes=preserve_quotes
    )

    try:
        path.write_text(new_source, encoding='utf-8')
    except OSError as exc:
        raise PatchError(f"Cannot write {path}: {exc}") from exc

    return result
