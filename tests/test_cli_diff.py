"""Tests for envoy.cli_diff."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from envoy.cli_diff import run_diff


@pytest.fixture()
def old_env_file(tmp_path: Path) -> Path:
    f = tmp_path / "old.env"
    f.write_text(
        "APP_NAME=myapp\n"
        "SECRET_KEY=old_secret\n"
        "REMOVED_KEY=gone\n",
        encoding="utf-8",
    )
    return f


@pytest.fixture()
def new_env_file(tmp_path: Path) -> Path:
    f = tmp_path / "new.env"
    f.write_text(
        "APP_NAME=myapp\n"
        "SECRET_KEY=new_secret\n"
        "ADDED_KEY=hello\n",
        encoding="utf-8",
    )
    return f


def test_run_diff_prints_to_stdout(
    old_env_file: Path, new_env_file: Path, capsys: pytest.CaptureFixture
) -> None:
    run_diff(str(old_env_file), str(new_env_file))
    captured = capsys.readouterr()
    assert "ADDED_KEY" in captured.out
    assert "REMOVED_KEY" in captured.out
    assert "SECRET_KEY" in captured.out


def test_run_diff_masks_secrets_by_default(
    old_env_file: Path, new_env_file: Path, capsys: pytest.CaptureFixture
) -> None:
    run_diff(str(old_env_file), str(new_env_file), mask_secrets=True)
    captured = capsys.readouterr()
    assert "old_secret" not in captured.out
    assert "new_secret" not in captured.out


def test_run_diff_no_mask_shows_values(
    old_env_file: Path, new_env_file: Path, capsys: pytest.CaptureFixture
) -> None:
    run_diff(str(old_env_file), str(new_env_file), mask_secrets=False)
    captured = capsys.readouterr()
    assert "old_secret" in captured.out or "new_secret" in captured.out


def test_run_diff_show_unchanged(
    old_env_file: Path, new_env_file: Path, capsys: pytest.CaptureFixture
) -> None:
    run_diff(str(old_env_file), str(new_env_file), show_unchanged=True)
    captured = capsys.readouterr()
    assert "APP_NAME" in captured.out


def test_run_diff_writes_to_file(
    old_env_file: Path, new_env_file: Path, tmp_path: Path
) -> None:
    out_file = tmp_path / "diff_output.txt"
    run_diff(str(old_env_file), str(new_env_file), output_file=str(out_file))
    content = out_file.read_text(encoding="utf-8")
    assert "ADDED_KEY" in content
    assert "REMOVED_KEY" in content


def test_run_diff_exit_nonzero_raises(
    old_env_file: Path, new_env_file: Path
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        run_diff(str(old_env_file), str(new_env_file), exit_nonzero=True)
    assert exc_info.value.code == 1


def test_run_diff_missing_file_exits(tmp_path: Path) -> None:
    existing = tmp_path / "exists.env"
    existing.write_text("KEY=val\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        run_diff(str(existing), str(tmp_path / "missing.env"))
    assert exc_info.value.code == 1
