"""Generate a schema (template) from an existing .env file."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envoy.parser import EnvParser


class SchemaGeneratorError(Exception):
    pass


_SECRET_PATTERNS = ("secret", "password", "passwd", "token", "key", "api", "auth", "private")


def _infer_required(value: str) -> bool:
    """Keys with non-empty values are assumed required."""
    return bool(value.strip())


def _infer_secret(name: str) -> bool:
    lower = name.lower()
    return any(p in lower for p in _SECRET_PATTERNS)


def generate_schema(
    env_path: str | Path,
    required_keys: Optional[List[str]] = None,
    optional_keys: Optional[List[str]] = None,
) -> Dict[str, object]:
    """Parse *env_path* and produce a JSON-schema dict compatible with
    ``envoy.validator``.  Caller may override required/optional lists;
    otherwise heuristics are applied.

    Returns a dict with keys:
        required  – list of required key names
        optional  – list of optional key names
        secrets   – list of key names inferred as secrets
    """
    path = Path(env_path)
    if not path.exists():
        raise SchemaGeneratorError(f"File not found: {path}")

    parser = EnvParser()
    try:
        pairs = parser.parse_file(str(path))
    except Exception as exc:  # pragma: no cover
        raise SchemaGeneratorError(f"Parse error: {exc}") from exc

    schema: Dict[str, object] = {"required": [], "optional": [], "secrets": []}

    for key, value in pairs.items():
        if required_keys is not None:
            bucket = "required" if key in required_keys else "optional"
        elif optional_keys is not None:
            bucket = "optional" if key in optional_keys else "required"
        else:
            bucket = "required" if _infer_required(value) else "optional"

        schema[bucket].append(key)  # type: ignore[attr-defined]

        if _infer_secret(key):
            schema["secrets"].append(key)  # type: ignore[attr-defined]

    return schema


def write_schema(
    schema: Dict[str, object],
    output_path: str | Path,
) -> None:
    """Serialise *schema* to a JSON file at *output_path*."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(schema, fh, indent=2)
        fh.write("\n")
