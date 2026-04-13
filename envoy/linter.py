"""Linter for .env files: checks style and convention issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envoy.parser import EnvParser


@dataclass
class LintIssue:
    line: int
    key: str
    code: str
    message: str
    severity: str = "warning"  # "warning" | "error"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] line {self.line} ({self.code}): {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    def summary(self) -> str:
        if not self.has_issues:
            return "No lint issues found."
        errors = sum(1 for i in self.issues if i.severity == "error")
        warnings = sum(1 for i in self.issues if i.severity == "warning")
        parts = []
        if errors:
            parts.append(f"{errors} error(s)")
        if warnings:
            parts.append(f"{warnings} warning(s)")
        return "Lint finished: " + ", ".join(parts) + "."


def lint(source: str) -> LintResult:
    """Run all lint checks on *source* text and return a LintResult."""
    result = LintResult()
    lines = source.splitlines()

    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(lines, start=1):
        stripped = raw.strip()

        # Skip blank lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        if "=" not in stripped:
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()

        # L001: key should be UPPER_SNAKE_CASE
        if key != key.upper():
            result.issues.append(LintIssue(
                line=lineno, key=key, code="L001",
                message=f"Key '{key}' should be uppercase.",
                severity="warning",
            ))

        # L002: no spaces around '='
        if raw.count(" = ") or ("= " in raw.split("#")[0] and not value.startswith(" ")):
            result.issues.append(LintIssue(
                line=lineno, key=key, code="L002",
                message=f"Avoid spaces around '=' for key '{key}'.",
                severity="warning",
            ))

        # L003: duplicate key
        if key in seen_keys:
            result.issues.append(LintIssue(
                line=lineno, key=key, code="L003",
                message=f"Duplicate key '{key}' (first seen on line {seen_keys[key]}).",
                severity="error",
            ))
        else:
            seen_keys[key] = lineno

        # L004: value contains unquoted whitespace
        val_stripped = value.strip()
        if val_stripped and not val_stripped.startswith(("'", '"')) and " " in val_stripped.split("#")[0]:
            result.issues.append(LintIssue(
                line=lineno, key=key, code="L004",
                message=f"Value for '{key}' contains spaces and should be quoted.",
                severity="warning",
            ))

    return result
