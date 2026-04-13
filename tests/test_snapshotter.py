"""Tests for envoy.snapshotter."""

import pytest
from pathlib import Path

from envoy.snapshotter import (
    Snapshot,
    SnapshotError,
    save_snapshot,
    load_snapshot,
    list_snapshots,
    delete_snapshot,
)


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path / "snapshots"


SAMPLE = {"DB_HOST": "localhost", "API_KEY": "secret123"}


def test_save_and_trip(snap_dir):
    save_snapshot("v1", SAMPLE, env_file=".env", snapshot_dir=snap_dir)
    snap1", snapshot_dir=snap_dir)
    assert snap.name == "v1"
    assert snap.values == SAMPLE
    assert snap.env_file == ".env"


def test_created_at_is_iso_string(snap_dir):
    snap = save_snapshot("ts", SAMPLE, snapshot_dir=snap_dir)
    assert "T" in snap.created_at  # ISO-8601 contains 'T'


def test_tags_stored_and_retrieved(snap_dir):
    save_snapshot("tagged", SAMPLE, tags=["production", "v2"], snapshot_dir=snap_dir)
    snap = load_snapshot("tagged", snapshot_dir=snap_dir)
    assert snap.tags == ["production", "v2"]


def test_load_missing_snapshot_raises(snap_dir):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot("ghost", snapshot_dir=snap_dir)


def test_list_snapshots_empty_dir(snap_dir):
    assert list_snapshots(snapshot_dir=snap_dir) == []


def test_list_snapshots_returns_all(snap_dir):
    save_snapshot("a", {"X": "1"}, snapshot_dir=snap_dir)
    save_snapshot("b", {"Y": "2"}, snapshot_dir=snap_dir)
    snaps = list_snapshots(snapshot_dir=snap_dir)
    names = [s.name for s in snaps]
    assert "a" in names and "b" in names


def test_list_snapshots_sorted_by_created_at(snap_dir):
    save_snapshot("first", {"A": "1"}, snapshot_dir=snap_dir)
    save_snapshot("second", {"B": "2"}, snapshot_dir=snap_dir)
    snaps = list_snapshots(snapshot_dir=snap_dir)
    assert snaps[0].created_at <= snaps[1].created_at


def test_delete_snapshot(snap_dir):
    save_snapshot("temp", SAMPLE, snapshot_dir=snap_dir)
    delete_snapshot("temp", snapshot_dir=snap_dir)
    with pytest.raises(SnapshotError):
        load_snapshot("temp", snapshot_dir=snap_dir)


def test_delete_missing_raises(snap_dir):
    with pytest.raises(SnapshotError, match="not found"):
        delete_snapshot("nope", snapshot_dir=snap_dir)


def test_snapshot_to_dict_and_from_dict():
    snap = Snapshot(name="x", env_file=".env", created_at="2024-01-01T00:00:00+00:00",
                    values={"K": "V"}, tags=["t"])
    restored = Snapshot.from_dict(snap.to_dict())
    assert restored.name == snap.name
    assert restored.values == snap.values
    assert restored.tags == snap.tags


def test_overwrite_existing_snapshot(snap_dir):
    save_snapshot("dup", {"A": "old"}, snapshot_dir=snap_dir)
    save_snapshot("dup", {"A": "new"}, snapshot_dir=snap_dir)
    snap = load_snapshot("dup", snapshot_dir=snap_dir)
    assert snap.values["A"] == "new"
