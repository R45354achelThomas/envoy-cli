"""Snapshot support: save and load named .env snapshots for later diffing."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_SNAPSHOT_DIR = Path(".env-snapshots")


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


@dataclass
class Snapshot:
    name: str
    env_file: str
    created_at: str
    values: Dict[str, str]
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "env_file": self.env_file,
            "created_at": self.created_at,
            "values": self.values,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            name=data["name"],
            env_file=data["env_file"],
            created_at=data["created_at"],
            values=data["values"],
            tags=data.get("tags", []),
        )


def _snapshot_path(snapshot_dir: Path, name: str) -> Path:
    safe = name.replace("/", "_").replace("\\", "_")
    return snapshot_dir / f"{safe}.json"


def save_snapshot(
    name: str,
    values: Dict[str, str],
    env_file: str = ".env",
    tags: Optional[List[str]] = None,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> Snapshot:
    """Persist a snapshot to disk; returns the saved Snapshot."""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    path = _snapshot_path(snapshot_dir, name)
    snap = Snapshot(
        name=name,
        env_file=env_file,
        created_at=datetime.now(timezone.utc).isoformat(),
        values=values,
        tags=tags or [],
    )
    path.write_text(json.dumps(snap.to_dict(), indent=2), encoding="utf-8")
    return snap


def load_snapshot(
    name: str,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> Snapshot:
    """Load a snapshot by name; raises SnapshotError if not found."""
    path = _snapshot_path(snapshot_dir, name)
    if not path.exists():
        raise SnapshotError(f"Snapshot '{name}' not found in {snapshot_dir}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Snapshot.from_dict(data)
    except (KeyError, json.JSONDecodeError) as exc:
        raise SnapshotError(
            f"Snapshot '{name}' is corrupt or has an unexpected format: {exc}"
        ) from exc


def list_snapshots(snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR) -> List[Snapshot]:
    """Return all snapshots stored in *snapshot_dir*, sorted by creation time."""
    if not snapshot_dir.exists():
        return []
    snaps = []
    for p in snapshot_dir.glob("*.json"):
        try:
            snaps.append(Snapshot.from_dict(json.loads(p.read_text(encoding="utf-8"))))
        except (KeyError, json.JSONDecodeError):
            continue
    return sorted(snaps, key=lambda s: s.created_at)


def delete_snapshot(
    name: str,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> None:
    """Delete a snapshot by name; raises SnapshotError if not found."""
    path = _snapshot_path(snapshot_dir, name)
