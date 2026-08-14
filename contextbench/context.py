"""Build a system prompt (Context Bundle) from a directory of markdown files, or None for bare."""
from __future__ import annotations

from pathlib import Path


def build_system_prompt(context_dir: str | None) -> str:
    """Concatenate every *.md file under context_dir, sorted by path, into one system prompt.

    context_dir=None (the "bare" Context Bundle) returns an empty string — no instructions,
    no persona, nothing. That's the whole point of the comparison.
    """
    if context_dir is None:
        return ""
    root = Path(context_dir).expanduser()
    if not root.is_dir():
        raise FileNotFoundError(f"context dir not found: {root}")
    parts = []
    for md in sorted(root.rglob("*.md")):
        parts.append(f"<!-- {md.relative_to(root)} -->\n{md.read_text()}")
    return "\n\n".join(parts)
