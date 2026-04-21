"""Classify .env keys into semantic categories (database, auth, network, etc.)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ClassifyError(Exception):
    """Raised when classification cannot proceed."""


_CATEGORY_PATTERNS: Dict[str, List[str]] = {
    "database": ["DB_", "DATABASE_", "POSTGRES", "MYSQL", "MONGO", "REDIS", "SQLITE"],
    "auth": ["AUTH_", "JWT_", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "API_KEY", "OAUTH"],
    "network": ["HOST", "PORT", "URL", "URI", "ENDPOINT", "ADDR", "ADDRESS", "DOMAIN"],
    "storage": ["S3_", "BUCKET", "STORAGE_", "BLOB_", "GCS_", "MINIO"],
    "logging": ["LOG_", "LOGGING_", "SENTRY_", "DATADOG_", "NEWRELIC_"],
    "feature": ["FEATURE_", "FLAG_", "ENABLE_", "DISABLE_", "FF_"],
    "email": ["MAIL_", "EMAIL_", "SMTP_", "SENDGRID_", "MAILGUN_"],
}

_UNCATEGORIZED = "uncategorized"


@dataclass
class ClassifyResult:
    categories: Dict[str, Dict[str, str]] = field(default_factory=dict)
    key_map: Dict[str, str] = field(default_factory=dict)

    def has_category(self, name: str) -> bool:
        return name in self.categories and bool(self.categories[name])

    def category_for(self, key: str) -> str:
        return self.key_map.get(key, _UNCATEGORIZED)

    def uncategorized(self) -> Dict[str, str]:
        return self.categories.get(_UNCATEGORIZED, {})

    def summary(self) -> str:
        lines = []
        for cat, entries in sorted(self.categories.items()):
            lines.append(f"{cat}: {len(entries)} key(s)")
        return "\n".join(lines) if lines else "no keys"


def _match_category(key: str) -> str:
    upper = key.upper()
    for category, patterns in _CATEGORY_PATTERNS.items():
        for pat in patterns:
            if upper.startswith(pat) or pat in upper:
                return category
    return _UNCATEGORIZED


def classify(
    env: Dict[str, str],
    custom_patterns: Optional[Dict[str, List[str]]] = None,
) -> ClassifyResult:
    """Classify each key in *env* into a semantic category.

    Args:
        env: Mapping of env-var keys to values.
        custom_patterns: Optional extra ``{category: [prefix, ...]}`` patterns
            that are checked *before* the built-in ones.

    Returns:
        A :class:`ClassifyResult` with keys grouped by category.
    """
    if not isinstance(env, dict):
        raise ClassifyError("env must be a dict")

    effective: Dict[str, List[str]] = {}
    if custom_patterns:
        effective.update({k: [p.upper() for p in v] for k, v in custom_patterns.items()})
    effective.update({k: v for k, v in _CATEGORY_PATTERNS.items() if k not in effective})

    categories: Dict[str, Dict[str, str]] = {}
    key_map: Dict[str, str] = {}

    for key, value in env.items():
        upper = key.upper()
        matched = _UNCATEGORIZED
        for category, patterns in effective.items():
            for pat in patterns:
                if upper.startswith(pat.upper()) or pat.upper() in upper:
                    matched = category
                    break
            if matched != _UNCATEGORIZED:
                break
        categories.setdefault(matched, {})[key] = value
        key_map[key] = matched

    return ClassifyResult(categories=categories, key_map=key_map)
