"""Validation logic for .env files against a schema/template."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ValidationError:
    key: str
    message: str

    def __str__(self) -> str:
        return f"[{self.key}] {self.message}"


@dataclass
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        lines = []
        if self.errors:
            lines.append(f"{len(self.errors)} error(s):")
            for e in self.errors:
                lines.append(f"  ERROR   {e}")
        if self.warnings:
            lines.append(f"{len(self.warnings)} warning(s):")
            for w in self.warnings:
                lines.append(f"  WARNING {w}")
        if not lines:
            lines.append("All checks passed.")
        return "\n".join(lines)


def validate(
    env: dict[str, str],
    template: dict[str, Optional[str]],
    allow_extras: bool = True,
) -> ValidationResult:
    """Validate *env* against *template*.

    Args:
        env: Parsed environment mapping (key -> value).
        template: Template mapping where a value of None means the key is
                  required but has no default; any string value is the default
                  and the key is considered optional.
        allow_extras: When False, keys present in *env* but absent from
                      *template* are reported as warnings.

    Returns:
        A :class:`ValidationResult` describing all errors and warnings found.
    """
    result = ValidationResult()

    for key, default in template.items():
        if key not in env:
            if default is None:
                # Required key missing
                result.errors.append(
                    ValidationError(key, "required key is missing")
                )
            else:
                result.warnings.append(
                    ValidationError(
                        key,
                        f"optional key is missing (default: {default!r})",
                    )
                )
        elif env[key] == "" and default is None:
            result.warnings.append(
                ValidationError(key, "required key is present but empty")
            )

    if not allow_extras:
        for key in env:
            if key not in template:
                result.warnings.append(
                    ValidationError(key, "key not defined in template")
                )

    return result
