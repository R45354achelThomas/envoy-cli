"""Export .env data to various formats (shell export, JSON, YAML, dotenv)."""

from __future__ import annotations

import json
from typing import Dict, Literal

ExportFormat = Literal["shell", "json", "yaml", "dotenv"]


class ExportError(Exception):
    """Raised when an export operation fails."""


def to_shell(env: Dict[str, str]) -> str:
    """Export env vars as shell export statements."""
    lines = []
    for key, value in sorted(env.items()):
        escaped = value.replace('"', '\\"')
        lines.append(f'export {key}="{escaped}"')
    return "\n".join(lines)


def to_json(env: Dict[str, str], indent: int = 2) -> str:
    """Export env vars as a JSON object."""
    return json.dumps(dict(sorted(env.items())), indent=indent)


def to_yaml(env: Dict[str, str]) -> str:
    """Export env vars as YAML key-value pairs (no external dependency)."""
    lines = []
    for key, value in sorted(env.items()):
        # Simple scalar quoting: quote if value contains special chars
        if any(c in value for c in (':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', '"', "'")):
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"')
        else:
            lines.append(f"{key}: {value}" if value else f"{key}: \"\"")
    return "\n".join(lines)


def to_dotenv(env: Dict[str, str]) -> str:
    """Export env vars back to .env format."""
    lines = []
    for key, value in sorted(env.items()):
        if " " in value or "#" in value or not value:
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines)


def export_env(env: Dict[str, str], fmt: ExportFormat) -> str:
    """Dispatch export to the requested format."""
    if fmt == "shell":
        return to_shell(env)
    elif fmt == "json":
        return to_json(env)
    elif fmt == "yaml":
        return to_yaml(env)
    elif fmt == "dotenv":
        return to_dotenv(env)
    else:
        raise ExportError(f"Unknown export format: {fmt!r}")
