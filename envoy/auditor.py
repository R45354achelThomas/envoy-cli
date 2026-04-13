"""Audit log for tracking .env file access and mutations."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


AUDIT_LOG_ENV_VAR = "ENVOY_AUDIT_LOG"
DEFAULT_AUDIT_LOG = ".envoy_audit.jsonl"


@dataclass
class AuditEntry:
    action: str          # e.g. "load", "diff", "merge", "export", "snapshot"
    target: str          # file or snapshot name involved
    user: str            # os.getlogin() or $USER
    timestamp: str       # ISO-8601
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "target": self.target,
            "user": self.user,
            "timestamp": self.timestamp,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            action=data["action"],
            target=data["target"],
            user=data["user"],
            timestamp=data["timestamp"],
            details=data.get("details", {}),
        )


def _log_path() -> Path:
    return Path(os.environ.get(AUDIT_LOG_ENV_VAR, DEFAULT_AUDIT_LOG))


def _current_user() -> str:
    return os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"


def record(action: str, target: str, details: Optional[dict] = None) -> AuditEntry:
    """Append one audit entry to the log file and return it."""
    entry = AuditEntry(
        action=action,
        target=target,
        user=_current_user(),
        timestamp=datetime.now(timezone.utc).isoformat(),
        details=details or {},
    )
    log_file = _log_path()
    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict()) + "\n")
    return entry


def read_log(limit: Optional[int] = None) -> List[AuditEntry]:
    """Return audit entries from the log file, newest-last."""
    log_file = _log_path()
    if not log_file.exists():
        return []
    entries: List[AuditEntry] = []
    with log_file.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(AuditEntry.from_dict(json.loads(line)))
    if limit is not None:
        entries = entries[-limit:]
    return entries
