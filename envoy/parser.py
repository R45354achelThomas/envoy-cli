"""Parser for .env files supporting comments, blank lines, and quoted values."""

import re
from typing import Dict, Tuple

ENV_LINE_RE = re.compile(
    r'^(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$'
)


class EnvParseError(Exception):
    """Raised when a .env file contains a malformed line."""

    def __init__(self, line_number: int, line: str, message: str) -> None:
        self.line_number = line_number
        self.line = line
        super().__init__(f"Line {line_number}: {message} -> {line!r}")


def _strip_inline_comment(value: str) -> str:
    """Remove trailing inline comment from an unquoted value."""
    idx = value.find(" #")
    if idx != -1:
        return value[:idx].rstrip()
    return value


def _unquote(value: str) -> str:
    """Strip surrounding single or double quotes and unescape inner quotes."""
    for quote in ('"', "'"):
        if value.startswith(quote) and value.endswith(quote) and len(value) >= 2:
            inner = value[1:-1]
            return inner.replace(f"\\{quote}", quote)
    return _strip_inline_comment(value)


def parse_env_string(content: str, strict: bool = False) -> Dict[str, str]:
    """Parse the text content of a .env file into a key/value dict.

    Args:
        content: Raw text of the .env file.
        strict: If True, raise EnvParseError on malformed lines instead of skipping.

    Returns:
        Ordered dict of environment variable names to their string values.
    """
    result: Dict[str, str] = {}
    for lineno, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Support optional 'export' prefix
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        match = ENV_LINE_RE.match(line)
        if not match:
            if strict:
                raise EnvParseError(lineno, raw_line, "Invalid syntax")
            continue
        key = match.group("key")
        value = _unquote(match.group("value").strip())
        result[key] = value
    return result


def parse_env_file(path: str, strict: bool = False) -> Dict[str, str]:
    """Read and parse a .env file from disk."""
    with open(path, "r", encoding="utf-8") as fh:
        return parse_env_string(fh.read(), strict=strict)


def serialize_env(env: Dict[str, str]) -> str:
    """Serialize a key/value dict back to .env file format."""
    lines = []
    for key, value in env.items():
        if any(c in value for c in (" ", "#", "'", '"')):
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"
