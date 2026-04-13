"""Parser for .env files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterator, Tuple


class EnvParseError(Exception):
    """Raised when a .env file cannot be parsed."""

    def __init__(self, message: str, line_number: int | None = None):
        self.line_number = line_number
        super().__init__(f"Line {line_number}: {message}" if line_number else message)


_COMMENT_RE = re.compile(r'(?<!\\)#.*$')
_KEY_VALUE_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)')


def _strip_inline_comment(value: str) -> str:
    """Remove unescaped inline comments from an unquoted value."""
    return _COMMENT_RE.sub("", value).rstrip()


def _unquote(value: str) -> str:
    """Strip surrounding quotes and unescape contents."""
    if len(value) >= 2:
        if value[0] == '"' and value[-1] == '"':
            return value[1:-1].replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
        if value[0] == "'" and value[-1] == "'":
            return value[1:-1]
    return value


def _iter_pairs(text: str) -> Iterator[Tuple[int, str, str]]:
    """Yield (line_number, key, raw_value) for each valid assignment."""
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Handle 'export KEY=VALUE' syntax
        if stripped.startswith("export "):
            stripped = stripped[7:].lstrip()
        match = _KEY_VALUE_RE.match(stripped)
        if not match:
            raise EnvParseError(f"Invalid syntax: {line!r}", lineno)
        key, raw = match.group(1), match.group(2).strip()
        yield lineno, key, raw


def parse_env_string(text: str) -> Dict[str, str]:
    """Parse a .env-formatted string and return a key→value mapping."""
    result: Dict[str, str] = {}
    for _lineno, key, raw in _iter_pairs(text):
        if raw and raw[0] in ('"', "'"):
            value = _unquote(raw)
        else:
            value = _strip_inline_comment(raw)
        result[key] = value
    return result


def parse_env_file(path: Path) -> Dict[str, str]:
    """Read a .env file from disk and parse it."""
    text = path.read_text(encoding="utf-8")
    return parse_env_string(text)
