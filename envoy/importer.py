"""Import env vars from external sources (shell environment, JSON, YAML)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


@dataclass
class ImportResult:
    env: Dict[str, str]
    source: str
    imported_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    def has_skipped(self) -> bool:
        return len(self.skipped_keys) > 0

    def summary(self) -> str:
        parts = [f"Imported {len(self.imported_keys)} key(s) from {self.source}"]
        if self.skipped_keys:
            parts.append(f"skipped {len(self.skipped_keys)} key(s)")
        return "; ".join(parts) + "."


def from_shell(
    keys: Optional[List[str]] = None,
    prefix: Optional[str] = None,
    strip_prefix: bool = False,
) -> ImportResult:
    """Import variables from the current shell environment."""
    env: Dict[str, str] = {}
    imported: List[str] = []
    skipped: List[str] = []

    candidates = dict(os.environ)

    for k, v in candidates.items():
        if prefix and not k.startswith(prefix):
            skipped.append(k)
            continue
        if keys and k not in keys:
            skipped.append(k)
            continue
        out_key = k[len(prefix):] if (strip_prefix and prefix) else k
        env[out_key] = v
        imported.append(out_key)

    return ImportResult(env=env, source="shell", imported_keys=imported, skipped_keys=skipped)


def from_json(text: str, keys: Optional[List[str]] = None) -> ImportResult:
    """Import variables from a JSON object string."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object.")

    env: Dict[str, str] = {}
    imported: List[str] = []
    skipped: List[str] = []

    for k, v in data.items():
        if keys and k not in keys:
            skipped.append(k)
            continue
        env[str(k)] = str(v)
        imported.append(str(k))

    return ImportResult(env=env, source="json", imported_keys=imported, skipped_keys=skipped)


def from_dotenv_text(text: str, keys: Optional[List[str]] = None) -> ImportResult:
    """Import variables from raw .env file text."""
    from envoy.parser import EnvParser  # local import to avoid circularity

    parser = EnvParser()
    parsed = parser.parse(text)

    env: Dict[str, str] = {}
    imported: List[str] = []
    skipped: List[str] = []

    for k, v in parsed.items():
        if keys and k not in keys:
            skipped.append(k)
            continue
        env[k] = v
        imported.append(k)

    return ImportResult(env=env, source="dotenv", imported_keys=imported, skipped_keys=skipped)
