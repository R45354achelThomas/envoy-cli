"""Template rendering: fill a .env.template file using a resolved env dict."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?::-([^}]*))?\s*\}\}")


class TemplateError(Exception):
    """Raised when template rendering fails."""

    def __init__(self, message: str, key: Optional[str] = None) -> None:
        super().__init__(message)
        self.key = key


def render(template: str, env: Dict[str, str], *, strict: bool = True) -> str:
    """Replace ``{{ KEY }}`` and ``{{ KEY:-default }}`` placeholders in *template*.

    Parameters
    ----------
    template:
        Raw template text containing ``{{ VAR }}`` placeholders.
    env:
        Mapping of variable names to their resolved values.
    strict:
        When *True* (default) a missing variable with no default raises
        :class:`TemplateError`.  When *False* the placeholder is left as-is.
    """
    errors: list[str] = []

    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        key = m.group(1)
        default = m.group(2)  # may be None
        if key in env:
            return env[key]
        if default is not None:
            return default
        if strict:
            errors.append(key)
            return m.group(0)  # keep placeholder so we can report all at once
        return m.group(0)

    result = _PLACEHOLDER_RE.sub(_replace, template)
    if errors:
        missing = ", ".join(errors)
        raise TemplateError(
            f"Template references undefined variable(s) with no default: {missing}",
            key=errors[0],
        )
    return result


def render_file(
    template_path: Path,
    env: Dict[str, str],
    *,
    strict: bool = True,
) -> str:
    """Read *template_path* and return the rendered string."""
    try:
        template = template_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TemplateError(f"Cannot read template file: {exc}") from exc
    return render(template, env, strict=strict)
