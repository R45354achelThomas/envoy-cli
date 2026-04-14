"""Compare two .env files across multiple dimensions and produce a structured report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.diff import compute_diff, DiffEntry
from envoy.validator import validate, ValidationResult
from envoy.linter import lint, LintResult


@dataclass
class ComparisonReport:
    """Aggregated result of comparing a base env against a target env."""

    base_path: str
    target_path: str
    diff_entries: List[DiffEntry] = field(default_factory=list)
    base_lint: Optional[LintResult] = None
    target_lint: Optional[LintResult] = None
    base_validation: Optional[ValidationResult] = None
    target_validation: Optional[ValidationResult] = None

    # ------------------------------------------------------------------ #
    # Convenience helpers
    # ------------------------------------------------------------------ #

    @property
    def added(self) -> List[DiffEntry]:
        return [e for e in self.diff_entries if e.kind == "added"]

    @property
    def removed(self) -> List[DiffEntry]:
        return [e for e in self.diff_entries if e.kind == "removed"]

    @property
    def changed(self) -> List[DiffEntry]:
        return [e for e in self.diff_entries if e.kind == "changed"]

    @property
    def has_lint_errors(self) -> bool:
        base_err = self.base_lint.has_errors() if self.base_lint else False
        target_err = self.target_lint.has_errors() if self.target_lint else False
        return base_err or target_err

    def summary(self) -> str:
        lines = [
            f"Comparison: {self.base_path}  →  {self.target_path}",
            f"  Added   : {len(self.added)}",
            f"  Removed : {len(self.removed)}",
            f"  Changed : {len(self.changed)}",
        ]
        if self.base_lint is not None:
            lines.append(f"  Base lint issues   : {len(self.base_lint.issues)}"),
        if self.target_lint is not None:
            lines.append(f"  Target lint issues : {len(self.target_lint.issues)}")
        return "\n".join(lines)


def compare(
    base: Dict[str, str],
    target: Dict[str, str],
    base_path: str = "<base>",
    target_path: str = "<target>",
    schema: Optional[Dict] = None,
    include_lint: bool = True,
    mask_secrets: bool = True,
) -> ComparisonReport:
    """Run a full comparison between *base* and *target* env dicts."""

    diff_entries = compute_diff(base, target, mask_secrets=mask_secrets)

    base_lint = lint(base_path) if include_lint else None
    target_lint = lint(target_path) if include_lint else None

    base_validation: Optional[ValidationResult] = None
    target_validation: Optional[ValidationResult] = None
    if schema is not None:
        base_validation = validate(base, schema)
        target_validation = validate(target, schema)

    return ComparisonReport(
        base_path=base_path,
        target_path=target_path,
        diff_entries=diff_entries,
        base_lint=base_lint,
        target_lint=target_lint,
        base_validation=base_validation,
        target_validation=target_validation,
    )
