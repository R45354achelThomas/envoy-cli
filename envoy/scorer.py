"""Score .env files for quality/security based on heuristics."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from envoy.diff import _is_secret


class ScoreError(Exception):
    pass


@dataclass
class ScoreIssue:
    key: str
    message: str
    severity: str  # 'warning' | 'error'

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class ScoreResult:
    env: Dict[str, str]
    issues: List[ScoreIssue] = field(default_factory=list)
    score: int = 100

    def has_issues(self) -> bool:
        return bool(self.issues)

    def summary(self) -> str:
        return f"Score: {self.score}/100 ({len(self.issues)} issue(s))"


def score(env: Dict[str, str]) -> ScoreResult:
    """Analyse env dict and return a ScoreResult with a quality score."""
    if not isinstance(env, dict):
        raise ScoreError("env must be a dict")

    issues: List[ScoreIssue] = []

    for key, value in env.items():
        # Secret keys should not be empty
        if _is_secret(key) and value == "":
            issues.append(ScoreIssue(key, "secret key has empty value", "error"))

        # Secret keys should not contain obvious placeholder text
        if _is_secret(key) and value.lower() in ("changeme", "secret", "password", "todo", "fixme", "xxx"):
            issues.append(ScoreIssue(key, f"secret key has weak placeholder value '{value}'", "error"))

        # Keys should be uppercase
        if key != key.upper():
            issues.append(ScoreIssue(key, "key is not uppercase", "warning"))

        # Values with unresolved template markers
        if "{{" in value or "}}" in value:
            issues.append(ScoreIssue(key, "value appears to contain unresolved template markers", "warning"))

    penalty = sum(10 if i.severity == "error" else 5 for i in issues)
    final_score = max(0, 100 - penalty)

    return ScoreResult(env=env, issues=issues, score=final_score)
